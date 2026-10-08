from ninja import Schema
from typing import Optional


class DeviceTokenSchema(Schema):
    token: str
    type: str = "web"


class SendNotificationSchema(Schema):
    user_id: int
    title: str
    message: str
    data: Optional[dict] = None