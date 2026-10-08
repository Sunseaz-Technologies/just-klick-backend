from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied






# mixin to restrict access to views based on user role
class RoleRequiredMixin(LoginRequiredMixin):

    required_roles = None

    def dispatch(self, request, *args, **kwargs):

        if not request.user.role:
            raise PermissionDenied(
                "Role not assigned."
            )

        if request.user.role.name.lower() not in [
            role.lower()
            for role in self.required_roles
        ]:
            raise PermissionDenied(
                "Permission denied."
            )

        return super().dispatch(
            request,
            *args,
            **kwargs
        )