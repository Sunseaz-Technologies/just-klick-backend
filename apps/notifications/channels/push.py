from firebase_admin import messaging

def send_push(token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        # Android-specific configuration
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                sound='custom_sound',           # Drops extension (.wav/.mp3) on Android
                channel_id='justklick-alerts'    # The channel matching the mobile setup
            )
        ),
        # iOS/APNs-specific configuration
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound='custom_sound.wav'     # Must include file extension for iOS
                )
            )
        ),
        token=token,
        data=data or {}
    )

    return messaging.send(message)
