from apps.notifications.models import Notification


def save_notification(user, title, message):

    return Notification.objects.create(user=user, title=title, message=message)
