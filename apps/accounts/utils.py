# accounts/utils.py
import random
import re
from datetime import timedelta
from django.utils import timezone
from .models import OTP
from .models import LoginHistory
import jwt
from django.conf import settings
from .models import BlacklistedToken
import requests

OTP_EXPIRY_MINUTES = 30
MAX_ATTEMPTS = 20
MAX_RESENDS = 10
OTP_PER_HOUR_LIMIT = 10
IP_PER_HOUR_LIMIT = 30
RESEND_COOLDOWN_SECONDS = 30
BLOCK_DURATION_HOURS = 1


def has_role(user, role_name):
    if not user or not user.is_authenticated:
        return False
    if not getattr(user, "role", None):
        return False
    return user.role.name.lower() == role_name.lower()


def check_phone_rate_limit(phone):

    one_hour_ago = timezone.now() - timedelta(hours=1)

    otp_count = OTP.objects.filter(phone=phone, created_at__gte=one_hour_ago).count()

    if otp_count >= OTP_PER_HOUR_LIMIT:
        return False

    return True


def check_ip_rate_limit(ip_address):

    if not ip_address:
        return True

    one_hour_ago = timezone.now() - timedelta(hours=1)

    otp_count = OTP.objects.filter(
        ip_address=ip_address, created_at__gte=one_hour_ago
    ).count()

    if otp_count >= IP_PER_HOUR_LIMIT:
        return False

    return True


def is_phone_blocked(phone):

    blocked = OTP.objects.filter(phone=phone, blocked_until__gt=timezone.now()).exists()

    return blocked


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp(phone, purpose):

    otp = generate_otp()

    OTP.objects.filter(phone=phone, purpose=purpose).delete()

    OTP.objects.create(
        phone=phone,
        otp=otp,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    message = f"Welcome to JustKlick. Your OTP for student registration is { otp }. Valid for 10 minutes. Do not share this OTP with anyone. sms"

    if not settings.SMS_API_KEY:
        raise ValueError("SMS_API_KEY is missing in environment variables")
    payload = {
        "key": settings.SMS_API_KEY.strip(),
        "type": "text" if len(message) <= 160 else "long",
        "contacts": phone,
        "senderid": settings.SMS_SENDER_ID.strip(),
        "peid": settings.SMS_PE_ID.strip(),
        "templateid": settings.SMS_TEMPLATE_ID.strip(),
        "msg": message,
    }

    try:
        requests.get(settings.SMS_API_URL.strip(), params=payload, timeout=10)

    except Exception as e:
        print("SMS ERROR:", str(e))

    print("\n" + "=" * 40)
    print("PHONE :", phone)
    print("OTP   :", otp)
    print("=" * 40 + "\n")
    return otp


def create_otp(phone, purpose, ip_address=None, user_agent=None):

    if is_phone_blocked(phone):
        return False, ("Too many failed attempts. " "Try again after 1 hour.")

    if not check_phone_rate_limit(phone):
        return False, ("Maximum OTP limit reached. " "Try again later.")

    if not check_ip_rate_limit(ip_address):
        return False, ("Too many requests from this IP.")

    otp_code = generate_otp()

    OTP.objects.create(
        phone=phone,
        otp=otp_code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    send_otp(phone, purpose)

    return True, "OTP sent successfully"


def validate_otp(phone, otp, purpose):

    otp_obj = (
        OTP.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not otp_obj:
        return False, "OTP not found"

    if otp_obj.blocked_until and otp_obj.blocked_until > timezone.now():
        return (False, "Too many failed attempts. Try again after 1 hour.")

    if otp_obj.expires_at < timezone.now():
        return False, "OTP expired"

    if otp_obj.attempts >= MAX_ATTEMPTS:
        return (False, "Maximum attempts exceeded. Try again after 1 hour.")

    if otp_obj.otp != otp:

        otp_obj.attempts += 1

        if otp_obj.attempts >= MAX_ATTEMPTS:

            otp_obj.blocked_until = timezone.now() + timedelta(
                hours=BLOCK_DURATION_HOURS
            )

            otp_obj.save(update_fields=["attempts", "blocked_until"])

            return (False, "Maximum attempts exceeded. Try again after 1 hour.")

        otp_obj.save(update_fields=["attempts"])

        remaining_attempts = MAX_ATTEMPTS - otp_obj.attempts

        return (False, f"Invalid OTP. {remaining_attempts} attempts remaining.")

    otp_obj.is_verified = True
    otp_obj.is_used = True
    otp_obj.verified_at = timezone.now()

    otp_obj.save(update_fields=["is_verified", "is_used", "verified_at"])

    return True, "OTP verified successfully"


def resend_otp(phone, purpose, ip_address=None, user_agent=None):

    last_otp = (
        OTP.objects.filter(phone=phone, purpose=purpose, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not last_otp:
        return False, "No active OTP found"

    if last_otp.expires_at < timezone.now():
        return False, "OTP expired"

    diff = (timezone.now() - last_otp.created_at).total_seconds()

    if diff < RESEND_COOLDOWN_SECONDS:

        wait_time = RESEND_COOLDOWN_SECONDS - int(diff)

        return False, (f"Please wait {wait_time} seconds")

    if last_otp.resend_count >= MAX_RESENDS:
        return False, ("Maximum resend limit reached")

    last_otp.resend_count += 1

    last_otp.save(update_fields=["resend_count"])

    send_otp(phone=phone, purpose=last_otp.purpose)

    return True, ("OTP resent successfully")


def create_login_history(request, user, login_type):
    LoginHistory.objects.create(
        user=user,
        login_type=login_type,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT"),
        is_success=True,
    )


def blacklist_token(refresh_token):

    payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])

    BlacklistedToken.objects.get_or_create(jti=payload["jti"])


def is_token_blacklisted(jti):

    return BlacklistedToken.objects.filter(jti=jti).exists()
