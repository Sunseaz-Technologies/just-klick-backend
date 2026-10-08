from .channels.database import DatabaseChannel
from .channels.email import EmailChannel
from .channels.push import PushChannel


class NotificationServices:

    CHANNELS = {
        "database": DatabaseChannel(),
        "email": EmailChannel(),
        "push": PushChannel(),
    }

    @classmethod
    def send(cls, user, title, message, channels, data=None):

        for channel in channels:

            handler = cls.CHANNELS.get(channel)

            if handler:
                handler.send(user, title, message, data or {})
