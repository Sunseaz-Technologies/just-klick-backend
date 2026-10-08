import json
from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from apps.businesses.models import (
    Business,
    BusinessImage,
    BusinessFieldValue,
    BusinessListingPlan,
    BusinessListingSubscription,
    BusinessListingPlanFeature,
)
from apps.categories.models import Category, CategoryField
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.dynamic.pagination import paginate_queryset
from django.http import JsonResponse
# payments history download code
import csv
from django.http import HttpResponse

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            "company_name",
            "category",
            "location",
            "address",
            "email",
            "phone",
            "whatsapp",
            "website",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["category"].empty_label = "— Select category —"
        self.fields["address"].required = False
        self.fields["whatsapp"].required = False
        self.fields["website"].required = False
        self.fields["description"].required = False


def get_categories_with_fields():
    categories_with_fields = {}
    for cat in Category.objects.filter(is_active=True):
        fields = list(
            cat.fields.filter(is_active=True)
            .order_by("order")
            .values(
                "id",
                "label",
                "field_type",
                "is_required",
                "order",
                "options",
                "placeholder",
                "show_as_filter",
            )
        )
        if fields:
            categories_with_fields[cat.id] = fields
    return categories_with_fields


def save_dynamic_fields(business, post_data, category):
    if not category:
        return
    fields = CategoryField.objects.filter(category=category, is_active=True)
    active_field_ids = []
    for field in fields:
        active_field_ids.append(field.pk)
        key = f"field_{field.pk}"
        if field.field_type == "checkbox":
            values = post_data.getlist(key)
            value = json.dumps(values) if values else None
        else:
            value = post_data.get(key, "").strip() or None
        BusinessFieldValue.objects.update_or_create(
            business=business,
            field=field,
            defaults={"value": value},
        )
    BusinessFieldValue.objects.filter(business=business).exclude(
        field_id__in=active_field_ids
    ).delete()


def parse_field_values(field_values):
    parsed = []
    for fv in field_values:
        value = fv.value
        if fv.field.field_type == "checkbox" and value:
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = [value]
        parsed.append(
            {
                "label": fv.field.label,
                "field_type": fv.field.field_type,
                "value": value,
            }
        )
    return parsed


# ─────────────────────────────────────────────
# Public Views
# ─────────────────────────────────────────────


class BusinessRegisterView(View):
    def get(self, request):
        form = BusinessForm()
        return render(request, "businesses/register.html", {"form": form})

    def post(self, request):
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save()
            for img in request.FILES.getlist("images"):
                BusinessImage.objects.create(business=business, image=img)
            save_dynamic_fields(business, request.POST, business.category)
            messages.success(
                request, "Registration submitted. We will review and get back to you."
            )
            return redirect("businesses:register")
        return render(request, "businesses/register.html", {"form": form})


# ─────────────────────────────────────────────
# Admin Dashboard Views
# ─────────────────────────────────────────────


class BusinessListView(LoginRequiredMixin, View):
    def get(self, request):
        qs = (
            Business.objects.select_related("category").prefetch_related("images").all()
        )

        q = request.GET.get("q", "").strip()
        status = request.GET.get("status", "")
        category = request.GET.get("category", "")
        location = request.GET.get("location", "").strip()  # ← add this

        if q:
            qs = qs.filter(company_name__icontains=q) | qs.filter(email__icontains=q)

        if status:
            qs = qs.filter(status=status)

        if category:
            qs = qs.filter(category_id=category)

        if location:  # ← add this
            qs = qs.filter(location__icontains=location)

        qs = qs.order_by("-id")

        businesses = paginate_queryset(request, qs, per_page=10)

        return render(
            request,
            "businesses/list.html",
            {
                "businesses": businesses,
                "page_obj": businesses,
                "active_tab": "businesses",
                "category_choices": Category.objects.filter(is_active=True),
            },
        )


class BusinessCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = BusinessForm()
        return render(
            request,
            "businesses/form.html",
            {
                "form": form,
                "active_tab": "businesses",
                "categories_with_fields": get_categories_with_fields(),
                "existing_values": {},
            },
        )

    def post(self, request):
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save()
            for img in request.FILES.getlist("images"):
                BusinessImage.objects.create(business=business, image=img)
            save_dynamic_fields(business, request.POST, business.category)
            messages.success(request, "Business added successfully.")
            return redirect("businesses:list")
        return render(
            request,
            "businesses/form.html",
            {
                "form": form,
                "active_tab": "businesses",
                "categories_with_fields": get_categories_with_fields(),
                "existing_values": {},
            },
        )


class BusinessDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        field_values = business.field_values.select_related("field").all()
        parsed_field_values = parse_field_values(field_values)
        return render(
            request,
            "businesses/detail.html",
            {
                "business": business,
                "active_tab": "businesses",
                "parsed_field_values": parsed_field_values,
            },
        )


class BusinessEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        form = BusinessForm(instance=business)
        existing_values = {
            fv.field_id: fv.value
            for fv in business.field_values.select_related("field").all()
        }
        return render(
            request,
            "businesses/form.html",
            {
                "form": form,
                "business": business,
                "active_tab": "businesses",
                "categories_with_fields": get_categories_with_fields(),
                "existing_values": existing_values,
            },
        )

    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        form = BusinessForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            for img in request.FILES.getlist("images"):
                BusinessImage.objects.create(business=business, image=img)
            save_dynamic_fields(business, request.POST, business.category)
            messages.success(
                request, f'"{business.company_name}" updated successfully.'
            )
            return redirect("businesses:list")
        existing_values = {
            fv.field_id: fv.value
            for fv in business.field_values.select_related("field").all()
        }
        return render(
            request,
            "businesses/form.html",
            {
                "form": form,
                "business": business,
                "active_tab": "businesses",
                "categories_with_fields": get_categories_with_fields(),
                "existing_values": existing_values,
            },
        )




class BusinessDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        return render(
            request,
            "businesses/delete.html",
            {
                "business": business,
                "active_tab": "businesses",
            },
        )

    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        name = business.company_name
        business.delete()
        messages.success(request, f'"{name}" deleted successfully.')
        return redirect("businesses:list")


class BusinessVerifyView(LoginRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        business.status = "verified"
        business.rejection_reason = None
        business.save()
        if business.user:
            try:
                from apps.notifications.tasks import send_notification_task
                send_notification_task(
                    user_id=business.user.id,
                    title="Business Listing Approved",
                    message=f"🎉 Congratulations! Your business listing '{business.company_name}' has been approved and is now active on JustKlick.",
                    channels=["database", "push"]
                )
            except Exception:
                pass
        messages.success(request, f'"{business.company_name}" has been verified.')
        return redirect("businesses:detail", pk=pk)


class BusinessRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        reason = request.POST.get("reason", "").strip()
        business.status = "rejected"
        business.rejection_reason = reason
        business.save()
        if business.user:
            try:
                from apps.notifications.tasks import send_notification_task
                reason_str = f" Reason: {reason}." if reason else ""
                send_notification_task(
                    user_id=business.user.id,
                    title="Business Listing Rejected",
                    message=f"❌ Your business listing '{business.company_name}' was rejected.{reason_str} Please modify your listing details and try again.",
                    channels=["database", "push"]
                )
            except Exception:
                pass
        messages.error(request, f'"{business.company_name}" has been rejected.')
        return redirect("businesses:detail", pk=pk)


class BusinessImageDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        img = get_object_or_404(BusinessImage, pk=pk)
        business_pk = img.business.pk
        img.delete()
        return redirect("businesses:edit", pk=business_pk)


# ─────────────────────────────────────────────────────────────────
# Admin: Business Listing Plans management
# ─────────────────────────────────────────────────────────────────


class BusinessListingPlanListView(LoginRequiredMixin, View):
    def get(self, request):
        plans = paginate_queryset(
            request,
            BusinessListingPlan.objects.order_by("-created_at"),
            per_page=10,
        )
        return render(
            request,
            "businesses/listing_plan_list.html",
            {
                "plans": plans,
                "page_obj": plans,
                "active_tab": "listing_plans",
            },
        )


class BusinessListingPlanCreateView(LoginRequiredMixin, View):

    def get(self, request):
        return render(
            request,
            "businesses/listing_plan_form.html",
            {
                "active_tab": "listing_plans",
            },
        )

    def post(self, request):
        name = request.POST.get("name", "").strip()
        price = request.POST.get("price", "").strip()
        validity_days = request.POST.get("validity_days", "").strip()
        description = request.POST.get("description", "").strip() or None
        is_active = request.POST.get("is_active") == "on"

        # Get all feature inputs
        features = request.POST.getlist("features")

        if not name or not price or not validity_days:
            messages.error(request, "Name, price and validity days are required.")
            return render(
                request,
                "businesses/listing_plan_form.html",
                {
                    "active_tab": "listing_plans",
                },
            )

        plan = BusinessListingPlan.objects.create(
            name=name,
            price=price,
            validity_days=validity_days,
            description=description,
            is_active=is_active,
        )

        # Save Features
        for feature in features:
            feature = feature.strip()
            if feature:
                BusinessListingPlanFeature.objects.create(
                    plan=plan,
                    feature=feature
                )

        try:
            from django.contrib.auth import get_user_model
            from apps.notifications.tasks import send_notification_task

            User = get_user_model()

            for student in User.objects.filter(role__name="Student"):
                send_notification_task(
                    user_id=student.id,
                    title="New Business Plan Created!",
                    message="Explore our business plans.",
                    channels=["database", "push"],
                )
        except Exception:
            pass

        messages.success(request, f'Plan "{name}" created successfully.')
        return redirect("businesses:listing_plan_list")


class BusinessListingPlanEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        plan = get_object_or_404(BusinessListingPlan, pk=pk)
        return render(
            request,
            "businesses/listing_plan_form.html",
            {
                "plan": plan,
                "active_tab": "listing_plans",
            },
        )

    def post(self, request, pk):
        plan = get_object_or_404(BusinessListingPlan, pk=pk)
        plan.name = request.POST.get("name", plan.name).strip()
        plan.price = request.POST.get("price", plan.price)
        plan.validity_days = request.POST.get("validity_days", plan.validity_days)
        plan.description = request.POST.get("description", "").strip() or None
        plan.is_active = request.POST.get("is_active") == "on"
        plan.save()

        # Get all feature inputs
        features = request.POST.getlist("features")

        # Replace old features with the submitted list
        plan.features.all().delete()
        for feature in features:
            feature = feature.strip()
            if feature:
                BusinessListingPlanFeature.objects.create(
                    plan=plan,
                    feature=feature
                )

        messages.success(request, f'Plan "{plan.name}" updated.')
        return redirect("businesses:listing_plan_list")


class BusinessListingPlanDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        plan = get_object_or_404(BusinessListingPlan, pk=pk)
        return render(
            request,
            "businesses/listing_plan_confirm_delete.html",
            {
                "plan": plan,
                "active_tab": "listing_plans",
            },
        )

    def post(self, request, pk):
        plan = get_object_or_404(BusinessListingPlan, pk=pk)
        name = plan.name
        plan.delete()
        messages.success(request, f'Plan "{name}" deleted.')
        return redirect("businesses:listing_plan_list")



 
 

class AdminBusinessPaymentHistoryView(View):
    """List all payment transactions."""
 
    def get(self, request):
        qs = BusinessListingSubscription.objects.select_related(
            "plan", "business", "vendor"
        ).order_by("-created_at")
 
        from django.db.models import Sum
        total_transactions = qs.count()
        success_count = qs.filter(payment_status='SUCCESS').count()
        pending_count = qs.filter(payment_status='PENDING').count()
        failed_count = qs.filter(payment_status='FAILED').count()
        total_income = qs.filter(payment_status='SUCCESS').aggregate(total=Sum('amount'))['total'] or 0

        payments = paginate_queryset(request, qs, per_page=10)
        return render(request, "businesses/admin_payment_history.html", {
            "payments": payments,
            "page_obj": payments,
            "active_tab": "payment_history",
            "total_transactions": total_transactions,
            "success_count": success_count,
            "pending_count": pending_count,
            "failed_count": failed_count,
            "total_income": total_income,
        })
 
 

class AdminPaymentDetailView(View):
    """Full page detail view — opened when admin clicks the eye icon."""

    def get(self, request, pk):
        from apps.accounts.models import User

        vendor = get_object_or_404(
            User,
            pk=pk,
            role__name__iexact="Vendor"
        )

        payment = (
            BusinessListingSubscription.objects
            .select_related("plan", "business", "vendor")
            .filter(vendor=vendor)
            .order_by("-created_at")
            .first()
        )

        if not payment:
            messages.warning(
                request,
                "No payment details found for this vendor."
            )
            return redirect("vendor_list")  # Replace with your vendors list URL name

        return render(
            request,
            "businesses/admin_payment_detail.html",
            {
                "payment": payment,
                "vendor": vendor,
            },
        )
 
 
from datetime import date as date_type
class AdminPaymentEditView(LoginRequiredMixin, View):

    def get(self, request, pk):
        from apps.accounts.models import User
        vendor = get_object_or_404(User, pk=pk, role__name__iexact="Vendor")
        subscription = BusinessListingSubscription.objects.filter(vendor=vendor).order_by("-created_at").first()
        return render(request, "businesses/admin_payement_edit.html", {
            "payment"   : subscription,
            "vendor"    : vendor,
            "active_tab": "vendor_list",
        })

    def post(self, request, pk):
        from apps.accounts.models import User
        vendor = get_object_or_404(User, pk=pk, role__name__iexact="Vendor")
        subscription = BusinessListingSubscription.objects.filter(vendor=vendor).order_by("-created_at").first()

        # Vendor fields
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name",  "").strip()

        # Payment fields
        payment_status      = request.POST.get("payment_status",      "").strip()
        amount              = request.POST.get("amount",              "").strip()
        razorpay_order_id   = request.POST.get("razorpay_order_id",   "").strip()
        razorpay_payment_id = request.POST.get("razorpay_payment_id", "").strip()
        razorpay_signature  = request.POST.get("razorpay_signature",  "").strip()

        # Subscription dates
        start_date = request.POST.get("start_date", "").strip() or None
        end_date   = request.POST.get("end_date",   "").strip() or None

        # Validate
        allowed_payment = {"SUCCESS", "PENDING", "FAILED"}
        if payment_status and payment_status not in allowed_payment:
            return JsonResponse({"success": False, "error": "Invalid payment status."})

        try:
            from datetime import date as date_type

            # Save vendor name
            if first_name:
                vendor.first_name = first_name
            if last_name:
                vendor.last_name = last_name
            vendor.save(update_fields=["first_name", "last_name"])

            # Save subscription fields
            if subscription:
                if payment_status:
                    subscription.payment_status = payment_status
                if amount:
                    subscription.amount = float(amount)
                if razorpay_order_id:
                    subscription.razorpay_order_id = razorpay_order_id
                if razorpay_payment_id:
                    subscription.razorpay_payment_id = razorpay_payment_id
                if razorpay_signature:
                    subscription.razorpay_signature = razorpay_signature

                subscription.start_date = date_type.fromisoformat(start_date) if start_date else None
                subscription.end_date   = date_type.fromisoformat(end_date)   if end_date   else None

                subscription.save(update_fields=[
                    "payment_status", "amount",
                    "razorpay_order_id", "razorpay_payment_id", "razorpay_signature",
                    "start_date", "end_date",
                ])

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
        
        
        

class AdminBusinessPaymentExportView(View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="payment_history.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "S No",
                "Vendor",
                "Phone",
                "Business",
                "Plan",
                "Amount",
                "Status",
                "Razorpay Order ID",
                "Start Date",
                "End Date",
                "Date",
            ]
        )

        payments = BusinessListingSubscription.objects.select_related(
            "plan", "business", "vendor"
        ).order_by("-created_at")

        for i, p in enumerate(payments, 1):
            writer.writerow(
                [
                    p.vendor.email,
                    p.vendor.phone or "—",
                    p.business.company_name,
                    p.plan.name,
                    p.amount,
                    p.payment_status,
                    p.razorpay_order_id,
                    p.start_date.strftime("%d %b %Y") if p.start_date else "—",
                    p.end_date.strftime("%d %b %Y") if p.end_date else "—",
                    p.created_at.strftime("%d %b %Y, %I:%M %p"),
                ]
            )

        return response
