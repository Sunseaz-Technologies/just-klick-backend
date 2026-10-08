from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from apps.notifications.servicess.notification_service import NotificationService
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import logout
from .models import Role, Lead, User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .utils import create_otp, validate_otp
from django.views.generic import ListView
from django.db.models import Q
from apps.businesses.models import Business, Category
from django.utils import timezone
from apps.dynamic.pagination import paginate_queryset
from apps.vendors.models import Review
from apps.notifications.tasks import send_notification_task
from apps.vendors.models import Review
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
import csv
from django.http import HttpResponse


User = get_user_model()


class AdminLoginView(View):
    template_name = "accounts/admin/admin_login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        # Fallback validation check
        if not email or not password:
            return JsonResponse(
                {"success": False, "message": "All fields are required."}, status=400
            )

        user = authenticate(request, email=email, password=password)

        if not user:
            return JsonResponse(
                {"success": False, "message": "Invalid credentials"}, status=400
            )

        if not user.is_superuser:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Access restricted. Admin privileges required.",
                },
                status=403,
            )

        login(request, user)
        # mark that a login push should be sent once the client registers
        try:
            request.session["send_login_push"] = True
            request.session["login_push_sent"] = False
            request.session.save()
        except Exception:
            pass
        send_notification_task(
            user_id=request.user.id,
            title="Hello Admin",
            message="welcome Back login success",
            channels=["database"],
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Login authorized", 
                "redirect_url": "/dashboard/",
            }
        )


class ForgotPasswordView(View):
    template_name = "accounts/admin/forgot_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip()

        if not email:
            return JsonResponse(
                {
                    "success": False,
                    "message": "A valid email address execution parameter is required.",
                },
                status=400,
            )

        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = (
                f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
            )

            email_message = (
                "Hello,\n\n"
                "We received a request to reset the password for your Admin account. "
                "Click the link below to configure your new credentials:\n\n"
                f"{reset_link}\n\n"
                "For security purposes, this initialization link will expire in 2 hours. "
                "If you did not make this request, please disregard this automated transmission safely.\n\n"
                "Regards,\n"
                "Justklick Team"
            )

            send_mail(
                subject="[Action Required] Reset Your Admin Password",
                message=email_message,
                from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
                recipient_list=[email],
                fail_silently=False,
            )
        except User.DoesNotExist:

            return JsonResponse(
                {
                    "success": False,
                    "message": "The requested identity trace was not located.",
                },
                status=404,
            )

        return JsonResponse(
            {
                "success": True,
                "message": "A secure password configuration link has been dispatched to your target inbox.",
            }
        )


class ResetPasswordView(View):
    template_name = "accounts/admin/reset_password.html"

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            valid_token = default_token_generator.check_token(user, token)
        except Exception:
            valid_token = False

        return render(
            request,
            self.template_name,
            {"valid_token": valid_token, "uidb64": uidb64, "token": token},
        )

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return JsonResponse(
                {
                    "success": False,
                    "message": "The dynamic authorization target link is structuralized incorrectly.",
                },
                status=400,
            )

        if not default_token_generator.check_token(user, token):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Authorization context configuration link expired.",
                },
                status=400,
            )

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not password or not confirm_password:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Credential verification targets are mandatory variables.",
                },
                status=400,
            )

        if password != confirm_password:
            return JsonResponse(
                {"success": False, "message": "Credentials structurally mismatch."},
                status=400,
            )

        user.set_password(password)
        user.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Security matrix configuration parsed and updated successfully.",
                "redirect_url": "/admin-login/",
            }
        )


class AdminLogoutView(View):

    def get(self, request):

        logout(request)

        return redirect("admin_login")


class VendorRegisterView(View):

    template_name = "accounts/vendor/vendor_register.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        action = request.POST.get("action")

        # ================= SEND OTP =================

        if action == "send_otp":

            first_name = request.POST.get("first_name", "").strip()

            last_name = request.POST.get("last_name", "").strip()

            email = request.POST.get("email", "").strip()

            phone = request.POST.get("phone", "").strip()

            ip_address = request.META.get("REMOTE_ADDR")

            user_agent = request.META.get("HTTP_USER_AGENT")

            # Email check

            if User.objects.filter(email=email).exists():

                messages.error(request, "Email already registered.")

                return render(
                    request,
                    self.template_name,
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                    },
                )

            # Mobile check

            existing_user = (
                User.objects.filter(phone=phone).select_related("role").first()
            )

            if existing_user:

                role_name = existing_user.role.name if existing_user.role else "User"

                messages.error(
                    request, f"This mobile number is already registered as {role_name}."
                )

                return render(
                    request,
                    self.template_name,
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                    },
                )

            success, message = create_otp(
                phone=phone,
                purpose="REGISTER",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if not success:

                messages.error(request, message)

                return render(
                    request,
                    self.template_name,
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                    },
                )

            request.session["register_first_name"] = first_name
            request.session["register_last_name"] = last_name
            request.session["register_email"] = email
            request.session["register_phone"] = phone

            messages.success(request, message)

            return render(
                request,
                self.template_name,
                {
                    "show_otp": True,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                },
            )

        # ================= REGISTER =================

        elif action == "register":

            otp = request.POST.get("otp", "").strip()

            first_name = request.session.get("register_first_name")

            last_name = request.session.get("register_last_name")

            email = request.session.get("register_email")

            phone = request.session.get("register_phone")

            success, message = validate_otp(
                phone=phone,
                otp=otp,
                purpose="REGISTER",
            )

            if not success:

                messages.error(request, message)

                return render(
                    request,
                    self.template_name,
                    {
                        "show_otp": True,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                    },
                )

            # Final safety check

            if User.objects.filter(phone=phone).exists():

                messages.error(request, "This mobile number is already registered.")

                return redirect("vendor-register")

            vendor_role, _ = Role.objects.get_or_create(name="Vendor")

            user = User.objects.create(
                email=email,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                role=vendor_role,
                is_phone_verified=True,
                is_active=True,
            )
            send_notification_task(
            user_id=request.user.id,
            title="Registration",
            message="Registration successful",
            channels=[
                "database",
                "push",
            ],  # <--- Triggers BOTH database log and browser push
        )

            request.session.flush()

            messages.success(request, "Registration successful. Please login.")

            return redirect("vendor-login")

        return redirect("vendor-register")


class VendorLoginView(View):

    template_name = "accounts/vendor/vendor_login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        action = request.POST.get("action")

        if action == "send_otp":

            phone = request.POST.get("phone", "").strip()

            ip_address = request.META.get("REMOTE_ADDR")

            user_agent = request.META.get("HTTP_USER_AGENT")

            user = User.objects.filter(phone=phone, role__name="Vendor").first()

            if not user:

                messages.error(request, "No vendor account found with this number.")

                return render(
                    request,
                    self.template_name,
                    {
                        "phone": phone,
                    },
                )

            success, message = create_otp(
                phone=phone,
                purpose="LOGIN",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            if not success:

                messages.error(request, message)

                return render(
                    request,
                    self.template_name,
                    {
                        "phone": phone,
                    },
                )

            messages.success(request, message)

            return render(
                request,
                self.template_name,
                {
                    "show_otp": True,
                    "phone": phone,
                },
            )

        elif action == "login":

            phone = request.POST.get("phone", "").strip()

            otp = request.POST.get("otp", "").strip()

            success, message = validate_otp(
                phone=phone,
                otp=otp,
                purpose="LOGIN",
            )

            if not success:

                messages.error(request, message)

                return render(
                    request,
                    self.template_name,
                    {
                        "show_otp": True,
                        "phone": phone,
                    },
                )
            user = User.objects.get(phone=phone)
            request.session.cycle_key()
            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            request.session["send_login_push"] = True
            request.session["login_push_sent"] = False

            try:
                from apps.notifications.tasks import send_notification_task
                send_notification_task(
                    user_id=user.id,
                    title="Login",
                    message="Welcome Back Login Successful",
                    channels=["database"],
                )
            except Exception:
                pass

            messages.success(request, "Welcome back! Login successful.")
            return redirect("vendors:vendor.dashboard")
        return redirect("vendor-login")


# lead view
class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "accounts/admin/admin_leads.html"
    context_object_name = "leads"
    paginate_by = 5

    def get_queryset(self):
        # 1. Check if this is an AJAX request to toggle the read status
        toggle_id = self.request.GET.get("toggle_status_id")
        target_mode = self.request.GET.get("target_mode")

        if toggle_id and target_mode:
            try:
                lead = Lead.objects.get(id=toggle_id)
                lead.is_read = target_mode == "read"
                lead.save()  # This actually saves the state to your database!
            except Lead.DoesNotExist:
                pass

        # 2. Continue with your existing query fetching and filtering
        queryset = (
            Lead.objects.filter(is_deleted=False)
            .select_related("business", "business__category")
            .order_by("-created_at")
        )

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        category = self.request.GET.get("category")
        company = self.request.GET.get("company")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(subject__icontains=search)
                | Q(message__icontains=search)
                | Q(business__company_name__icontains=search)
            )

        if status == "read":
            queryset = queryset.filter(is_read=True)
        elif status == "unread":
            queryset = queryset.filter(is_read=False)

        if category:
            queryset = queryset.filter(business__category_id=category)

        if company:
            queryset = queryset.filter(business_id=company)

        return queryset

    def get_context_data(self, **kwargs):
        # Clean up the syntax error at the end of your original context view
        context = super().get_context_data(**kwargs)

        # Capture parameters to pass cleanly to template
        selected_category = self.request.GET.get("category")
        context["selected_status"] = self.request.GET.get(
            "status"
        )  # Added to remember selection

        context["categories"] = Category.objects.all()

        if selected_category and selected_category.isdigit():
            companies = Business.objects.filter(category_id=int(selected_category))
        else:
            companies = Business.objects.none()

        context["companies"] = companies
        return context


# soft delete view


@login_required
def lead_delete(request, pk):

    lead = get_object_or_404(Lead, pk=pk)

    lead.is_deleted = True
    lead.save()

    return redirect("admin-leads")


class DeletedLeadListView(LoginRequiredMixin, ListView):

    model = Lead
    template_name = "accounts/admin/admin_trash.html"
    context_object_name = "leads"

    def get_queryset(self):

        return (
            Lead.objects.filter(is_deleted=True)
            .select_related("business", "business__category")
            .order_by("-updated_at")
        )


@login_required
def restore_lead(request, pk):

    lead = get_object_or_404(Lead, pk=pk)

    lead.is_deleted = False
    lead.save()

    return redirect("trash")


@login_required
def permanent_delete_lead(request, pk):

    lead = get_object_or_404(Lead, pk=pk, is_deleted=True)

    lead.delete()

    return redirect("trash")


# leads export


class LeadExportCSVView(LoginRequiredMixin, View):

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leads.csv"'

        writer = csv.writer(response)

        # Header row
        writer.writerow(
            [
                "S.No",
                "Name",
                "Email",
                "Phone",
                "Subject",
                "Message",
                "Company",
                "Category",
                "Status",
                "Date",
            ]
        )

        leads = (
            Lead.objects.filter(is_deleted=False)
            .select_related("business", "business__category")
            .order_by("-created_at")
        )

        # Same filters as LeadListView
        search = request.GET.get("search")
        status = request.GET.get("status")
        category = request.GET.get("category")
        company = request.GET.get("company")

        if search:
            leads = leads.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(subject__icontains=search)
                | Q(message__icontains=search)
                | Q(business__company_name__icontains=search)
            )
        if status == "read":
            leads = leads.filter(is_read=True)
        elif status == "unread":
            leads = leads.filter(is_read=False)
        if category:
            leads = leads.filter(business__category_id=category)
        if company:
            leads = leads.filter(business_id=company)

        for i, lead in enumerate(leads, start=1):
            writer.writerow(
                [
                    i,
                    lead.name,
                    lead.email,
                    lead.phone,
                    lead.subject,
                    lead.message,
                    lead.business.company_name if lead.business else "—",
                    (
                        lead.business.category.name
                        if lead.business and lead.business.category
                        else "—"
                    ),
                    "Read" if lead.is_read else "Unread",
                    lead.created_at.strftime("%d %b %Y"),
                ]
            )

        return response


# superadmin reviews


class AdminReviewListView(LoginRequiredMixin, ListView):

    model = Review
    template_name = "accounts/admin/admin_reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):

        queryset = Review.objects.select_related(
            "user", "business", "business__user"
        ).order_by("-created_at")

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        rating = self.request.GET.get("rating")

        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search)
                | Q(business__company_name__icontains=search)
                | Q(review__icontains=search)
            )

        if status:
            queryset = queryset.filter(status=status)

        if rating:
            queryset = queryset.filter(rating=rating)

        return queryset

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        reviews = Review.objects.all()

        context["total_reviews"] = reviews.count()
        context["pending_reviews"] = reviews.filter(status="pending").count()
        context["approved_reviews"] = reviews.filter(status="approved").count()
        context["rejected_reviews"] = reviews.filter(status="rejected").count()

        return context


@login_required
def admin_approve_review(request, pk):

    review = get_object_or_404(Review, pk=pk)

    review.status = "approved"
    review.approved_at = timezone.now()

    review.save()

    return redirect("admin-reviews")


@login_required
def admin_reject_review(request, pk):

    review = get_object_or_404(Review, pk=pk)

    review.status = "rejected"

    review.save()

    return redirect("admin-reviews")


@login_required
def admin_delete_review(request, pk):

    review = get_object_or_404(Review, pk=pk)

    review.delete()

    return redirect("admin-reviews")


# admin profile
class AdminProfileView(View):
    template_name = "accounts/admin/profile_update.html"

    def get(self, request):

        return render(request, self.template_name, {"user_obj": request.user})

    def post(self, request):
        user = request.user

        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)

        if request.POST.get("delete_profile_image") == "true":
            if user.profile_image:
                user.profile_image.delete(save=False)
            user.profile_image = None
        elif request.FILES.get("profile_image"):
            user.profile_image = request.FILES.get("profile_image")

        current_password = request.POST.get("current_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        user.profile_image = request.FILES.get("profile_image")

        # Password Fields
        current_password = request.POST.get("current_password", "").strip()

        new_password = request.POST.get("new_password", "").strip()

        confirm_password = request.POST.get("confirm_password", "").strip()

        # Change Password Only If User Entered Password Fields
        if current_password or new_password or confirm_password:
            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
                return redirect("admin_profile")

            if not new_password:
                messages.error(request, "Please enter a new password.")
                return redirect("admin_profile")

            if new_password != confirm_password:
                messages.error(
                    request, "New password and confirm password do not match."
                )
                return redirect("admin_profile")

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")
            return redirect("admin_profile")

        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("admin_profile")


class VendorLogoutView(View):

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return redirect("vendor-login")
