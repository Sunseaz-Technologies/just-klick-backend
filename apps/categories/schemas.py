from ninja import Schema
from typing import Optional, List, Any


class CategoryFieldSchema(Schema):
    id: int
    label: str
    field_key: str
    field_type: str
    options: Optional[Any] = None
    show_as_filter: bool
    is_required: bool
    order: int

class CategorySchema(Schema):
    id: int
    name: str
    slug: str
    image: Optional[str] = None
    banner_image: Optional[str] = None
    subtitle: Optional[str] = None
    url: Optional[str] = None
    color: Optional[str] = None
    is_card: bool
    order: int
    is_active: bool
    fields: List[CategoryFieldSchema] = []

    @staticmethod
    def resolve_image(obj, context):
        if obj.image:
            request = context.get("request") if context else None
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    @staticmethod
    def resolve_banner_image(obj, context):
        if obj.banner_image:
            request = context.get("request") if context else None
            if request:
                return request.build_absolute_uri(obj.banner_image.url)
            return obj.banner_image.url
        return None