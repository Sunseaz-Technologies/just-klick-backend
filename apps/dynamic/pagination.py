
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate_queryset(request, queryset, per_page=10):
    """
    Reusable pagination helper.

    Usage:
        users = paginate_queryset(request, User.objects.all())
    """

    paginator = Paginator(queryset, per_page)

    page = request.GET.get("page", 1)

    try:
        page_obj = paginator.page(page)

    except PageNotAnInteger:
        page_obj = paginator.page(1)

    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj