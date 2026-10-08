from ninja import Router
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from .models import Notification
from .schemas import DeviceTokenSchema, SendNotificationSchema
from .servicess.notification_service import NotificationService
from .servicess.device_service import DeviceService
from apps.accounts.auth import CustomJWTAuth
from ninja.security import django_auth

router = Router(tags=["Notifications"])


# ─────────────────────────────────────────────
# POST /api/notifications/save-device-token
# Register / update the FCM device token for the
# currently authenticated user.
# ─────────────────────────────────────────────
@router.post("/save-device-token",auth=[CustomJWTAuth(), django_auth])
def save_device_token(request, payload: DeviceTokenSchema):
    """
    Save or update the FCM device token for the logged-in user.
    Required field in .env  : (none — uses firebase-service-account.json)
    Required in settings.py : FCM_DJANGO_SETTINGS
    """
    if not request.user.is_authenticated:
        return {"success": False, "error": "Not authenticated"}

    DeviceService.save_token(
        user=request.user,
        token=payload.token,
        device_type=payload.type,
    )

    # Send a one-time login push notification only when the login flow set
    # `send_login_push` in session (set on successful login). Also ensure we
    # don't resend by checking `login_push_sent`.
    try:
        send_flag = bool(request.session.get("send_login_push", False))
        already_sent = bool(request.session.get("login_push_sent", False))
    except Exception:
        send_flag = False
        already_sent = True

    if send_flag and not already_sent:
        NotificationService.notify_user(
            user=request.user,
            title="Login Successful",
            message="Welcome back! You are now logged in.",
            channels=["push"],
        )
        try:
            request.session["login_push_sent"] = True
            # clear the send flag so subsequent token updates won't trigger
            request.session.pop("send_login_push", None)
            request.session.save()
        except Exception:
            # session backend may be disabled; ignore silently
            pass

    return {"success": True, "message": "Device token saved successfully"}


# ─────────────────────────────────────────────
# POST /api/notifications/send-login-push
# Send a login success push to the currently authenticated user.
@router.post("/send-login-push",auth=[CustomJWTAuth(), django_auth])
def send_login_push(request):
    """
    Send a login success push notification to the current user.
    """
    if not request.user.is_authenticated:
        return {"success": False, "error": "Not authenticated"}

    NotificationService.notify_user(
        user=request.user,
        title="Login Successful",
        message="Welcome back! You are now logged in.",
        channels=["push"],
    )

    return {"success": True, "message": "Login push notification sent"}


# ─────────────────────────────────────────────
# POST /api/notifications/send
# Send a push + database notification to any user.
# Only accessible by admin / staff users.
# ─────────────────────────────────────────────
@router.post("/send",auth=[CustomJWTAuth(), django_auth])
def send_notification(request, payload: SendNotificationSchema):
    """
    Send a notification to a specific user by user_id.
    Saves the notification to the DB and sends a FCM push notification.

    Required IDs / keys (add to .env):
      - Firebase service account JSON file at  credentials/firebase-service-account.json
      - FCM_DJANGO_SETTINGS block in settings.py  (see settings note below)
    """
    if not request.user.is_authenticated:
        return {"success": False, "error": "Not authenticated"}

    if not request.user.is_staff:
        return {"success": False, "error": "Permission denied — staff only"}

    try:
        target_user = User.objects.get(id=payload.user_id)
    except User.DoesNotExist:
        return {"success": False, "error": f"User {payload.user_id} not found"}

    NotificationService.notify_user(
        user=target_user,
        title=payload.title,
        message=payload.message,
        data=payload.data or {},
    )

    return {
        "success": True,
        "message": f"Notification sent to user {payload.user_id}",
    }


# ─────────────────────────────────────────────
# GET /api/notifications/list
# List all notifications for the logged-in user.
# ─────────────────────────────────────────────
@router.get("/list", auth=[CustomJWTAuth(), django_auth])
def list_notifications(request):
    """
    Returns all notifications for the currently authenticated user,
    newest first.
    """
    notifications = (
        Notification.objects.filter(user=request.user)
        .order_by("-created_at")
        .values("id", "title", "message", "is_read", "created_at")
    )

    return {
        "success": True,
        "notifications": list(notifications),
    }


# ─────────────────────────────────────────────
# PATCH /api/notifications/{notification_id}/mark-read
# Mark a single notification as read.
# ─────────────────────────────────────────────
@router.patch("/{notification_id}/mark-read",auth=[CustomJWTAuth(), django_auth])
def mark_notification_read(request, notification_id: int):
    """
    Mark a specific notification as read for the logged-in user.
    """
    if not request.user.is_authenticated:
        return {"success": False, "error": "Not authenticated"}

    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])

    return {"success": True, "message": "Notification marked as read"}


# ─────────────────────────────────────────────
# PATCH /api/notifications/mark-all-read
# Mark ALL notifications for the logged-in user as read.
# ─────────────────────────────────────────────
@router.patch("/mark-all-read",auth=[CustomJWTAuth(), django_auth])
def mark_all_notifications_read(request):
    """
    Bulk mark all notifications as read for the logged-in user.
    """
    if not request.user.is_authenticated:
        return {"success": False, "error": "Not authenticated"}

    updated = Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True
    )

    return {"success": True, "updated_count": updated}


@router.delete("/delete/{notification_id}", auth=[CustomJWTAuth(), django_auth])
def notification_delete(request, notification_id: int):
    """
    Delete a specific notification.
    """

    notification = Notification.objects.filter(
        id=notification_id,
        user=request.user
    ).first()

    if not notification:
        return {
            "success": False,
            "error": "Notification not found"
        }

    notification.delete()

    return {
        "success": True,
        "message": "Notification deleted successfully"
    }