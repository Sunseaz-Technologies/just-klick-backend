from functools import wraps
from django.core.exceptions import PermissionDenied

def role_permission_required(permission_codename):
    """
    Decorator for views that checks whether the current active role in session has a specific permission.
    If the role lacks permission, it raises a PermissionDenied exception (which results in a 403 response).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from apps.roles.views import get_current_role, auto_initialize
            # Ensure DB is initialized
            auto_initialize()
            
            role = get_current_role(request)
            if role:
                if role.name == 'Super Admin' or role.permissions.filter(codename=permission_codename).exists():
                    return view_func(request, *args, **kwargs)
                
            raise PermissionDenied("You do not have permission to access this page.")
        return _wrapped_view
    return decorator
