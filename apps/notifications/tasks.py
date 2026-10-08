from apps.accounts.models import User

from .servicess.notification_service import NotificationService


def send_notification_task(user_id, title, message, channels=None, data=None):

    user = User.objects.get(id=user_id)

    NotificationService.notify_user(
        user=user,
        title=title,
        message=message,
        channels=channels,
        data=data,
    )
