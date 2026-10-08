# apps/accounts/decorators.py

from functools import wraps
from django.shortcuts import render, redirect


def superadmin_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:

            return render(
                request,
                "403.html",
                status=403
            )

        return view_func(request, *args, **kwargs)

    return wrapper