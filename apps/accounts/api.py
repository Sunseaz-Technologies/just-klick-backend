from django.contrib.auth import get_user_model, login as django_login
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render
from google.oauth2 import id_token
from google.auth.transport import requests
from ninja import Router
from ninja_jwt.tokens import RefreshToken
from django.conf import settings
from .models import Role, StudentOnboarding, Lead, OTP
from apps.businesses.models import Business
from .schemas import *
from .utils import create_otp, validate_otp, resend_otp, send_otp
from .utils import create_login_history
from random import randint
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from ninja_jwt.authentication import JWTAuth
from .auth import CustomJWTAuth
from .utils import blacklist_token

jwt_auth = CustomJWTAuth()
router = Router()
User = get_user_model()


# =========================================================================
#  GOOGLE OAUTH ENDPOINTS
# =========================================================================


@router.post("/google-auth", response=AuthTokenOut)
def google_auth_verify(request, data: GoogleAuthIn):
    try:
        id_info = id_token.verify_oauth2_token(
            data.id_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )

        email = id_info.get("email")
        first_name = id_info.get("given_name", "")
        last_name = id_info.get("family_name", "")

        if not email:
            return AuthTokenOut(
                success=False,
                message="Email claim missing from Google credential.",
            )

        role, _ = Role.objects.get_or_create(name="Student")

        user = User.objects.filter(email=email).first()
        if user:
            if not user.role:
                user.role = role
            if not user.google_sub:
                user.google_sub = id_info.get("sub")
            user.is_email_verified = True

            google_picture = id_info.get("picture")
            if google_picture and not user.profile_image:
                user.profile_image = google_picture
            user.save()

            django_login(request, user)
            create_login_history(request, user, "GOOGLE")
            try:
                from apps.notifications.tasks import send_notification_task
                send_notification_task(
                    user_id=user.id,
                    title="Login Successful",
                    message="You have successfully logged in to JustKlick.",
                    channels=["database", "push"]
                )
            except Exception:
                pass

            refresh = RefreshToken.for_user(user)
            onboarding_done = StudentOnboarding.objects.filter(user=user).exists()
            return AuthTokenOut(
                success=True,
                status="success",
                access=str(refresh.access_token),
                refresh=str(refresh),
                message="Login successful.",
                onboarding_complete=onboarding_done,
            )

        return AuthTokenOut(
            success=False,
            status="not_registered",
            message="No account found for this Google email. Please register first.",
        )

    except ValueError as e:
        return AuthTokenOut(
            success=False,
            message=f"Invalid Google token: {str(e)}",
        )
    except Exception as e:
        return AuthTokenOut(success=False, message=f"Authentication error: {str(e)}")


# =========================================================================
#  OTP AUTHENTICATION PIPELINES
# =========================================================================


@router.post("/register/send-otp", response=MessageOut)
def register_send_otp(request, payload: SendOTPIn):
    q_filter = Q(phone=payload.phone)
    if payload.email:
        q_filter |= Q(email=payload.email)

    existing_user = User.objects.filter(q_filter).first()
    if existing_user:
        if existing_user.phone == payload.phone:
            return {
                "success": False,
                "message": "User with this phone number already exists. Please login.",
            }
        else:
            return {
                "success": False,
                "message": "User with this email address already exists. Please login.",
            }

    create_otp(
        phone=payload.phone,
        purpose="REGISTER",
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
    )

    return {"success": True, "message": "OTP sent successfully"}


@router.post("/register/verify-otp", response=MessageOut)
def register_verify_otp(request, payload: VerifyOTPIn):

    status, message = validate_otp(
        phone=payload.phone, otp=payload.otp, purpose="REGISTER"
    )

    return {"success": status, "message": message}


@router.post("/login/send-otp")
def login_send_otp(request, payload: SendOTPIn):

    user = User.objects.filter(phone=payload.phone).select_related("role").first()

    if not user:
        return {
            "success": False,
            "message": "Student account not found. Please register first.",
        }

    if not user.is_active:
        return {
            "success": False,
            "message": "This account has been disabled. Please contact support.",
        }

    if not user.role:
        return {"success": False, "message": "No role assigned to this account."}

    if user.role.name != "Student":
        return {
            "success": False,
            "message": (
                f"This mobile number is registered as {user.role.name}. "
                f"Please use {user.role.name} Login."
            ),
        }

    success, message = create_otp(
        phone=payload.phone,
        purpose="LOGIN",
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
    )

    return {"success": success, "message": message}


@router.post("/login/verify-otp", response=MessageOut)
def login_verify_otp(request, payload: VerifyOTPIn):

    status, message = validate_otp(
        phone=payload.phone, otp=payload.otp, purpose="LOGIN"
    )

    return {"success": status, "message": message}


@router.post("/resend-otp", response=MessageOut)
def resend_otp_view(request, payload: ResendOTPIn):

    status, message = resend_otp(
        phone=payload.phone,
        purpose=payload.purpose,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
    )

    return {"success": status, "message": message}


@router.post("/token/refresh")
def token_refresh(request, payload: TokenRefreshIn):
    try:
        refresh = RefreshToken(payload.refresh_token)
        return {"success": True, "access": str(refresh.access_token)}
    except Exception:
        return {"success": False, "message": "Invalid or expired refresh token"}


# email sending
@router.post("/send-email-login-otp")
def send_email_login_otp(request, email: str):

    try:
        user = User.objects.filter(email=email, role__name="Student").first()

        if not user:
            return {"success": False, "message": "Student account not found."}

        latest_otp = (
            OTP.objects.filter(email=email, purpose="LOGIN", is_used=False)
            .order_by("-created_at")
            .first()
        )

        # 30 second resend protection
        if latest_otp:

            seconds = (timezone.now() - latest_otp.created_at).total_seconds()

            if seconds < 30:

                return {
                    "success": False,
                    "message": (
                        f"Please wait {int(30-seconds)} seconds before requesting another OTP."
                    ),
                }

        # Max 10 OTPs per day
        today_count = OTP.objects.filter(
            email=email, purpose="LOGIN", created_at__date=timezone.now().date()
        ).count()

        if today_count >= 10:

            return {
                "success": False,
                "message": ("Maximum OTP requests reached for today."),
            }

        otp_code = str(randint(100000, 999999))

        OTP.objects.create(
            email=email,
            otp=otp_code,
            purpose="LOGIN",
            expires_at=timezone.now() + timedelta(minutes=10),
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        send_mail(
            subject="JustKlik - Login Verification Code",
            message=f"""
Hello,

We received a request to sign in to your JustKlik account.

Your One-Time Password (OTP) is:

{otp_code}

This verification code is valid for 10 minutes.

Security Tips:
• Never share this code with anyone.
• JustKlik staff will never ask for your OTP.
• If you did not request this login, please ignore this email.

Thank you,
JustKlik Support Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return {
            "success": True,
            "message": ("Verification code sent to your registered email."),
            "expires_in": 600,
            "resend_after": 30,
        }

    except Exception as e:

        print("=" * 50)
        print("EMAIL OTP ERROR")
        print(str(e))
        print("=" * 50)

        return {"success": False, "message": str(e)}


def validate_email_otp(email, otp, purpose="LOGIN"):

    otp_obj = (
        OTP.objects.filter(email=email, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not otp_obj:
        return (False, "Verification code not found.")

    if timezone.now() > otp_obj.expires_at:

        otp_obj.is_used = True
        otp_obj.save()

        return (False, "Verification code has expired.")

    if otp_obj.attempts >= 5:

        return (False, "Maximum verification attempts exceeded.")

    if otp_obj.otp != otp:

        otp_obj.attempts += 1
        otp_obj.save()

        remaining = 5 - otp_obj.attempts

        return (False, f"Invalid verification code. {remaining} attempts remaining.")

    otp_obj.is_verified = True
    otp_obj.is_used = True
    otp_obj.verified_at = timezone.now()
    otp_obj.save()

    return (True, "Verification successful.")


# =========================================================================
#  STANDARD FORM ACCOUNT AUTHENTICATION SUBMISSIONS
# =========================================================================


@router.post("/student-register")
def register(request, payload: StudentRegisterIn):
    otp_valid, otp_message = validate_otp(
        phone=payload.phone, otp=payload.otp, purpose="REGISTER"
    )
    if not otp_valid:
        return {
            "success": False,
            "status": "otp_invalid",
            "message": otp_message,
        }

    existing_user = User.objects.filter(
        Q(email=payload.email) | Q(phone=payload.phone)
    ).first()

    if existing_user:
        if existing_user.email == payload.email:
            return {
                "success": False,
                "status": "already_registered",
                "message": "User with this email already exists.",
            }
        return {
            "success": False,
            "status": "already_registered",
            "message": "User with this phone already exists.",
        }

    role, _ = Role.objects.get_or_create(name="Student")

    user = User.objects.create_user(
        username=payload.email,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        role=role,
        is_phone_verified=True,
    )
    try:
        from apps.notifications.tasks import send_notification_task
        send_notification_task(
            user_id=user.id,
            title="Registration Successful",
            message="Welcome to JustKlick! Your registration was successful.",
            channels=["database"]
        )
    except Exception:
        pass

    refresh = RefreshToken.for_user(user)

    return {
        "success": True,
        "message": "Registration complete!",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "onboarding_complete": False,
    }


@router.post("/student-login")
def login(request, payload: StudentLoginIn):
    user = None

    if payload.phone:
        user = User.objects.filter(phone=payload.phone, role__name="Student").first()
        if not user:
            return {"success": False, "message": "Student account not found."}
        success, message = validate_otp(
            phone=payload.phone, otp=payload.otp, purpose="LOGIN"
        )

    elif payload.email:
        user = User.objects.filter(email=payload.email, role__name="Student").first()
        if not user:
            return {"success": False, "message": "Student account not found."}
        success, message = validate_email_otp(
            email=payload.email, otp=payload.otp, purpose="LOGIN"
        )

    else:
        return {"success": False, "message": "Phone or email is required."}

    if not success:
        return {"success": False, "message": message}

    create_login_history(request, user, "OTP")
    try:
        from apps.notifications.tasks import send_notification_task
        send_notification_task(
            user_id=user.id,
            title="Login Successful",
            message="You have successfully logged in to JustKlick.",
            channels=["database", "push"]
        )
    except Exception:
        pass
    refresh = RefreshToken.for_user(user)
    onboarding_done = StudentOnboarding.objects.filter(user=user).exists()

    return {
        "success": True,
        "message": "Login successful.",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "onboarding_complete": onboarding_done,
    }


# =========================================================================
# VIEW PAGE ROUTE RENDERING
# =========================================================================


@router.get("/student-register")
def student_register_page(request):
    return render(
        request,
        "accounts/student/student_register.html",
        {"google_client_id": settings.GOOGLE_CLIENT_ID},
    )


@router.get("/student-login")
def student_login_page(request):
    return render(
        request,
        "accounts/student/student_login.html",
        {"google_client_id": settings.GOOGLE_CLIENT_ID},
    )


@router.get("/dashboard")
def dashboard(request):
    return render(request, "dashboard.html")


@router.get("/student-login-redirect")
def student_redirect(request):
    return render(request, "accounts/student/after_login_redirect.html")


@router.get("/student-onboarding-form")
def student_onboarding_page(request):
    return render(request, "accounts/student/student_onboarding.html")


# ==================================
# student-onboard details end-points
# ==================================


@router.post("/student-onboarding", auth=jwt_auth)
def student_onboarding(request, payload: StudentOnboardingSchema):

    user = request.user

    StudentOnboarding.objects.update_or_create(
        user=user,
        defaults={
            "father_name": payload.father_name,
            "college_code": payload.college_code,
            "dept_course": payload.course,
            "academic_year": payload.academic_year,
            "year_of_study": payload.year_of_study,
            "cgpa_percentage": payload.cgpa_percentage,
            "course_reason": payload.course_reason,
            "area_of_interest": payload.area_of_interest,
            "skills_to_develop": payload.skills_to_develop,
            "plan_after_graduation": payload.plan_after_graduation,
            "interested_abroad": payload.interested_abroad,
            "preferred_country": payload.preferred_country,
            "career_goal": payload.career_goal,
            "internship_completed": payload.internship_completed,
            "interested_in_internship": payload.interested_in_internship,
            "certifications": payload.certifications,
        },
    )
    try:
        from apps.notifications.tasks import send_notification_task
        send_notification_task(
            user_id=user.id,
            title="Onboarding Completed",
            message="Thank you for completing your onboarding! You can now explore matching opportunities and listings.",
            channels=["database", "push"]
        )
    except Exception:
        pass

    return {"success": True, "message": "Onboarding completed successfully"}


# ===========================
# student profile
# ==========================


@router.get("/student-profile", auth=jwt_auth)
def student_profile(request):

    user = request.user

    onboarding = StudentOnboarding.objects.filter(user=user).first()

    if not onboarding:
        return {"success": False, "message": "Profile not found"}

    return {
        "success": True,
        "data": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "father_name": onboarding.father_name,
            "college_code": onboarding.college_code,
            "dept_course": onboarding.dept_course,
            "academic_year": onboarding.academic_year,
            "year_of_study": onboarding.year_of_study,
            "cgpa_percentage": onboarding.cgpa_percentage,
            "course_reason": onboarding.course_reason,
            "area_of_interest": onboarding.area_of_interest,
            "skills_to_develop": onboarding.skills_to_develop,
            "plan_after_graduation": onboarding.plan_after_graduation,
            "interested_abroad": onboarding.interested_abroad,
            "preferred_country": onboarding.preferred_country,
            "career_goal": onboarding.career_goal,
            "internship_completed": onboarding.internship_completed,
            "interested_in_internship": onboarding.interested_in_internship,
            "certifications": onboarding.certifications,
        },
    }


# =====================
# student profile edit
# =====================
@router.put("/student-profile-update", auth=jwt_auth)
def update_student_profile(request, payload: StudentProfileUpdateSchema):

    onboarding = StudentOnboarding.objects.filter(user=request.user).first()

    if not onboarding:
        return {"success": False, "message": "Profile not found"}

    onboarding.father_name = payload.father_name
    onboarding.college_code = payload.college_code
    onboarding.dept_course = payload.dept_course
    onboarding.academic_year = payload.academic_year
    onboarding.year_of_study = payload.year_of_study
    onboarding.cgpa_percentage = payload.cgpa_percentage
    onboarding.course_reason = payload.course_reason
    onboarding.area_of_interest = payload.area_of_interest
    onboarding.skills_to_develop = payload.skills_to_develop
    onboarding.plan_after_graduation = payload.plan_after_graduation
    onboarding.interested_abroad = payload.interested_abroad
    onboarding.preferred_country = payload.preferred_country
    onboarding.career_goal = payload.career_goal
    onboarding.internship_completed = payload.internship_completed
    onboarding.interested_in_internship = payload.interested_in_internship
    onboarding.certifications = payload.certifications
    onboarding.save()
    try:
        from apps.notifications.tasks import send_notification_task
        send_notification_task(
            user_id=request.user.id,
            title="Profile Updated",
            message="Your student profile details have been successfully updated.",
            channels=["database", "push"]
        )
    except Exception:
        pass

    return {"success": True, "message": "Profile updated successfully"}


# ===========
# enquary
# ===========
@router.post("/submit-lead")
def submit_lead(request, payload: LeadSchema):

    business = Business.objects.filter(id=payload.business_id).first()

    if not business:
        return {"success": False, "message": "Business not found"}

    Lead.objects.create(
        business=business,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        message=payload.message,
    )
    try:
        user = User.objects.filter(Q(email=payload.email) | Q(phone=payload.phone)).first()
        if user:
            from apps.notifications.tasks import send_notification_task
            send_notification_task(
                user_id=user.id,
                title="Enquiry Submitted Successfully",
                message="Your enquiry was submitted successfully. We will get back to you soon.",
                channels=["database", "push"]
            )
        # Notify Business Owner (Vendor)
        if business.user:
            from apps.notifications.tasks import send_notification_task
            send_notification_task(
                user_id=business.user.id,
                title="New Enquiry Received",
                message=f"💼 You have received a new enquiry for your business '{business.company_name}' from {payload.name}.",
                channels=["database", "push"]
            )
    except Exception:
        pass

    return {"success": True, "message": "Enquiry submitted successfully"}


# ============================
# student logout api-endpoint
# ============================
@router.post("/student-logout", auth=jwt_auth)
def student_logout(request, payload: LogoutSchema):

    blacklist_token(payload.refresh_token)

    return {"success": True, "message": "Logout successful."}
