from fcm_django.models import FCMDevice


class DeviceService:

    @staticmethod
    def save_token(user, token, device_type="web"):
        """
        Save or update an FCM device token for a user.
        FCMDevice field is `registration_id` (not `token`).
        device_type choices: android | ios | web
        """
        FCMDevice.objects.update_or_create(
            registration_id=token,
            defaults={
                "user": user,
                "type": device_type,
                "active": True,
            },
        )
