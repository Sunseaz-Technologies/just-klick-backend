from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Permission
from django.contrib import messages
from django.db.models import Q
from apps.accounts.models import User, Role, StudentOnboarding
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from apps.accounts.decorators import superadmin_required
from apps.dynamic.pagination import paginate_queryset
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.crypto import get_random_string
import re
import csv
from django.http import HttpResponse


@login_required
@superadmin_required
def dashboard(request):

    if not request.user.is_superuser:

        messages.success(
            request, "You do not have permission to access the Admin Dashboard."
        )

        return redirect(
            "vendors:vendor.dashboard"
        )  # change to your vendor dashboard url name

    return render(request, "dashboard.html")


@login_required
@superadmin_required
def roles(request):

    if not request.user.is_superuser:
        return HttpResponseForbidden("You are not authorized to access this page.")

    search = request.GET.get("search", "")

    roles_queryset = Role.objects.all()

    if search:
        roles_queryset = roles_queryset.filter(name__icontains=search)

    roles_queryset = roles_queryset.order_by("name")

    roles = paginate_queryset(request, roles_queryset, per_page=10)

    context = {
        "roles": roles,
        "page_obj": roles,
        "search": search,
    }

    return render(request, "roles.html", context)


@login_required
@superadmin_required
def delete_role(request, role_id):

    role = get_object_or_404(Role, id=role_id)

    if request.method == "POST":
        role_name = role.name
        role.delete()

        messages.success(request, f'Role "{role_name}" deleted successfully.')

    return redirect("roles")


@login_required
@superadmin_required
def permissions(request, role_id):

    role = get_object_or_404(Role, id=role_id)

    search = request.GET.get("search", "")

    permissions = Permission.objects.all()

    if search:
        permissions = permissions.filter(name__icontains=search)

    permissions = permissions.order_by("content_type__app_label", "name")

    if request.method == "POST":

        selected_permissions = request.POST.getlist("permissions")

        role.permissions.set(selected_permissions)

        messages.success(request, "Permissions updated successfully.")

        return redirect("permissions", role_id=role.id)

    context = {
        "role": role,
        "permissions": permissions,
        "search": search,
    }

    return render(request, "permissions.html", context)


@login_required
@superadmin_required
def add_new_role(request):

    if request.method == "POST":

        role_name = request.POST.get("role_name")

        if not role_name:
            messages.error(request, "Role name is required.")
            return redirect("newrole")

        if Role.objects.filter(name=role_name).exists():
            messages.error(request, "Role already exists.")
            return redirect("newrole")

        Role.objects.create(name=role_name)

        messages.success(request, "Role created successfully.")
        return redirect("roles")

    return render(request, "add_new_role.html")


@login_required
@superadmin_required
def users(request):

    if request.method == "POST":

        user_id = request.POST.get("user_id")
        role_id = request.POST.get("role_id")

        user = User.objects.get(id=user_id)

        if role_id:
            user.role = Role.objects.get(id=role_id)
        else:
            user.role = None

        user.save()

        messages.success(request, f"Role assigned to {user.email}")

        return redirect("users")

    # Search
    search = request.GET.get("search", "").strip()

    users_queryset = User.objects.filter(is_superuser=False)

    if search:
        users_queryset = users_queryset.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    users_queryset = users_queryset.order_by("-id")

    users = paginate_queryset(request, users_queryset, per_page=5)

    context = {
        "users": users,
        "page_obj": users,
        "roles": Role.objects.exclude(name__iexact="superAdmin"),
        "search": search,
    }

    return render(request, "users.html", context)


@login_required
@superadmin_required
def student_list(request):
    q = request.GET.get("q", "").strip()

    search = request.GET.get("search", "").strip()

    students_queryset = User.objects.filter(
        role__name__iexact="Student", is_superuser=False
    )

    if search:
        students_queryset = students_queryset.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    students_queryset = students_queryset.order_by("-id")

    if q:
        students_queryset = students_queryset.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)  |
            Q(email__icontains=q)      |
            Q(phone__icontains=q)
        )

    # CSV export
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="students.csv"'
        writer = csv.writer(response)
        writer.writerow(["S.No", "Name", "Email", "Phone"])
        for i, student in enumerate(students_queryset, start=1):
            writer.writerow([
                i,
                student.get_full_name() or student.username,
                student.email,
                student.phone or "—",
            ])
        return response

    students = paginate_queryset(request, students_queryset, per_page=10)

    context = {
        "students" : students,
        "page_obj" : students,
        "q"        : q,
        "search": search,
    }
    return render(request, "students.html", context)


@login_required
@superadmin_required
def student_details(request, user_id):

    student = get_object_or_404(
        User.objects.select_related("student_onboarding"),
        id=user_id,
        role__name__iexact="Student",
        is_superuser=False,
    )

    context = {
        "student": student,
    }

    return render(request, "student_details.html", context)


@login_required
@superadmin_required
def edit_student(request, user_id):

    student = get_object_or_404(User, id=user_id)
    onboarding = StudentOnboarding.objects.filter(user=student).first()

    if onboarding is None:
        messages.success(request, "This student has not completed onboarding yet.")
        return redirect("student_list")

    if request.method == "POST":

        # User Details
        student.first_name = request.POST.get("first_name")
        student.last_name = request.POST.get("last_name")
        student.email = request.POST.get("email")

        # Student Details
        onboarding.father_name = request.POST.get("father_name")
        onboarding.college_code = request.POST.get("college_code")
        onboarding.dept_course = request.POST.get("dept_course")
        onboarding.academic_year = request.POST.get("academic_year")
        onboarding.year_of_study = request.POST.get("year_of_study")
        onboarding.cgpa_percentage = request.POST.get("cgpa_percentage")
        onboarding.plan_after_graduation = request.POST.get("plan_after_graduation")
        onboarding.interested_abroad = request.POST.get("interested_abroad")
        onboarding.preferred_country = request.POST.get("preferred_country")
        onboarding.career_goal = request.POST.get("career_goal")

        onboarding.internship_completed = (
            request.POST.get("internship_completed") == "True"
        )
        onboarding.interested_in_internship = (
            request.POST.get("interested_in_internship") == "True"
        )
        onboarding.certifications = request.POST.get("certifications") == "True"

        student.save()
        onboarding.save()

        messages.success(request, "Student details updated successfully.")

        return redirect("student_details", user_id=student.id)

    context = {
        "student": student,
        "onboarding": onboarding,
    }

    return render(request, "edit_student.html", context)


@login_required
@superadmin_required
def block_user(request, user_id):

    user = get_object_or_404(User, id=user_id)

    user.is_active = False
    user.save()

    messages.success(request, f"{user.email} blocked successfully.")

    return redirect("users")


@login_required
@superadmin_required
def unblock_user(request, user_id):

    user = get_object_or_404(User, id=user_id)

    user.is_active = True
    user.save()

    messages.success(request, f"{user.email} unblocked successfully.")

    return redirect("users")


@login_required
@superadmin_required
def delete_user(request, user_id):

    user = get_object_or_404(User, id=user_id)

    email = user.email

    user.delete()

    messages.success(request, f"{email} deleted successfully.")

    return redirect("users")


@login_required
@superadmin_required
def create_user(request):

    roles = Role.objects.all()

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()
        role_id = request.POST.get("role")

        # Username Validation
        if not username:
            messages.error(request, "Username is required.")
            return redirect("create_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("create_user")

        # Email Validation
        if not email:
            messages.error(request, "Email is required.")
            return redirect("create_user")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("create_user")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("create_user")

        # Phone Validation
        if not phone:
            messages.error(request, "Phone number is required.")
            return redirect("create_user")

        if not re.match(r"^[6-9]\d{9}$", phone):
            messages.error(request, "Enter a valid 10-digit mobile number.")
            return redirect("create_user")

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists.")
            return redirect("create_user")

        # Password Validation (Optional)
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                messages.error(request, ", ".join(e.messages))
                return redirect("create_user")
        else:
            # Auto-generate password if left blank
            password = get_random_string(12)

        # Role Validation
        role = None

        if role_id:
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                messages.error(request, "Selected role does not exist.")
                return redirect("create_user")

        try:

            user = User.objects.create_user(
                username=username,
                email=email,
                phone=phone,
                password=password,
            )

            user.role = role
            user.save()

            messages.success(request, f"User '{user.email}' created successfully.")

            return redirect("users")

        except Exception as e:

            messages.error(request, f"Error creating user: {str(e)}")

            return redirect("create_user")

    return render(request, "create_user.html", {"roles": roles})


@login_required
@superadmin_required
def vendor_list(request):
 
    search = request.GET.get("q", "").strip()
 
    vendors_queryset = User.objects.filter(
        role__name__iexact="Vendor", is_superuser=False
    ).order_by("-id")
 
    if search:
        vendors_queryset = vendors_queryset.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
 
    vendors = paginate_queryset(request, vendors_queryset, per_page=20)
 
    context = {
        "vendors": vendors,
        "page_obj": vendors,
    }
 
    return render(request, "businesses/vendor_list.html", context)




 
@login_required
@superadmin_required
def vendor_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="vendors.csv"'
 
    writer = csv.writer(response)
 
    # Header row
    writer.writerow([
        "S.No", "First Name", "Last Name", "Email", "Phone", "Joined"
    ])
 
    search = request.GET.get("q", "").strip()
 
    vendors = User.objects.filter(
        role__name__iexact="Vendor", is_superuser=False
    ).order_by("-id")
 
    if search:
        vendors = vendors.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
 
    for i, vendor in enumerate(vendors, start=1):
        writer.writerow([
            i,
            vendor.first_name or "—",
            vendor.last_name or "—",
            vendor.email,
            vendor.phone or "—",
            vendor.date_joined.strftime("%d %b %Y"),
        ])
 
    return response
 