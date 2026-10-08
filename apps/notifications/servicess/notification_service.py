import logging
from fcm_django.models import FCMDevice

from apps.notifications.channels.push import send_push
from apps.notifications.channels.database import save_notification
from apps.notifications.channels.email import send_email_notification

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def notify_user(user, title, message, data=None, channels=None):
        """
        Send notifications through the requested channels.

        Supported channels:
          - database: save notification record
          - push: send FCM push to registered devices
          - email: send email notification if user.email exists
        """
        channels = channels or ["database", "push"]
        str_data = {k: str(v) for k, v in (data or {}).items()}

        if "database" in channels:
            try:
                save_notification(user=user, title=title, message=message)
            except Exception as e:
                logger.error(f"Failed to save database notification: {e}")

        if "push" in channels:
            devices = FCMDevice.objects.filter(user=user, active=True)
            for device in devices:
                try:
                    send_push(device.registration_id, title, message, str_data)
                except Exception as e:
                    logger.error(f"Failed to send FCM push: {e}")

        if "email" in channels and getattr(user, "email", None):
            try:
                send_email_notification(title, message, user.email)
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

    @staticmethod
    def send_push(user, title, body, data=None):
        str_data = {k: str(v) for k, v in (data or {}).items()}
        devices = FCMDevice.objects.filter(user=user, active=True)
        for device in devices:
            try:
                send_push(device.registration_id, title, body, str_data)
            except Exception as e:
                logger.error(f"Failed to send FCM push to device {device.id}: {e}")

