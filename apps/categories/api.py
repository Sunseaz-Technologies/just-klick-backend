from ninja import Router
from .models import Category
from .schemas import CategorySchema

router = Router()


@router.get("/", response=list[CategorySchema])
def list_categories(request):
    return Category.objects.filter(is_active=True).prefetch_related("fields")