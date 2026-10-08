import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.conf import settings as django_settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.businesses.models import (
    Business, BusinessImage, BusinessFieldValue,
    BusinessListingPlan, BusinessListingSubscription,
)
from apps.categories.models import Category, CategoryField
from apps.advertisements.models import AdvertisementPayment, VendorAdvertisementSubscription
from apps.advertisements.models import VendorAdvertisementSubscription
from django.views.generic import ListView
from .models import Review
from django.db.models import Q, Avg
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from apps.dynamic.pagination import paginate_queryset
import razorpay

from django.contrib.auth import update_session_auth_hash

razorpay_client = razorpay.Client(
    auth=(django_settings.RAZORPAY_KEY_ID, django_settings.RAZORPAY_KEY_SECRET)
)



class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            'company_name', 'category', 'location', 'address',
            'email', 'phone', 'whatsapp', 'website',
            'description',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = '— Select category —'
        self.fields['address'].required = False
        self.fields['whatsapp'].required = False
        self.fields['website'].required = False
        self.fields['description'].required = False


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_categories_with_fields():
    categories_with_fields = {}
    for cat in Category.objects.filter(is_active=True):
        fields = CategoryField.objects.filter(category=cat, is_active=True).order_by('order')
        if fields.exists():
            categories_with_fields[cat.id] = list(fields.values(
                'id', 'label', 'field_type', 'is_required', 'order', 'options', 'show_as_filter'
            ))
    return categories_with_fields


def save_dynamic_fields(request, business):
    if not business.category:
        return
    fields = CategoryField.objects.filter(category=business.category, is_active=True)
    active_field_ids = []

    for field in fields:
        active_field_ids.append(field.pk)

        if field.field_type == 'checkbox':
            values = request.POST.getlist(f'field_{field.pk}')
            value = json.dumps(values) if values else None
        else:
            value = request.POST.get(f'field_{field.pk}', '').strip() or None

        BusinessFieldValue.objects.update_or_create(
            business=business,
            field=field,
            defaults={'value': value}
        )

    BusinessFieldValue.objects.filter(
        business=business
    ).exclude(field_id__in=active_field_ids).delete()


# ─────────────────────────────────────────────
# Vendor Views
# ─────────────────────────────────────────────




class VendorDashboardView(LoginRequiredMixin, View):

    def get(self, request):
        businesses = (
            Business.objects
            .select_related('category')
            .filter(user=request.user)
        )

        # payments = (
        #     AdvertisementPayment.objects
        #     .filter(vendor=request.user)
        #     .select_related('plan')
        #     .order_by('-created_at')
        # )

        subscription = (
            VendorAdvertisementSubscription.objects
            .filter(vendor=request.user)
            .select_related('plan')
            .order_by('-id')
            .first()
        )

        return render(
            request,
            'vendors/dashboard.html',
            {
                'businesses': businesses,
                'total_businesses': businesses.count(),
                'verified_businesses': businesses.filter(status='verified').count(),
                'pending_businesses': businesses.filter(status='pending').count(),
                'subscription': subscription,
                'active_tab': 'vendor.dashboard',
            }
        )




class VendorMyBusinessesView(LoginRequiredMixin, View):

    def get(self, request):
        queryset = (
            Business.objects
            .select_related('category')
            .filter(user=request.user)
            .order_by('-id')
        )

        businesses = paginate_queryset(
            request,
            queryset,
            per_page=10
        )

        return render(request, 'vendors/my_businesses.html', {
            'businesses': businesses,
            'page_obj': businesses,
            'active_tab': 'my_businesses',
        })


class VendorAddBusinessView(LoginRequiredMixin, View):

    def get(self, request):
        form = BusinessForm()
        return render(request, 'vendors/add_business.html', {
            'form': form,
            'categories_with_fields': get_categories_with_fields(),
            'submitted_values': {},
            'active_tab': 'add_business',
        })

    def post(self, request):
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.user = request.user
            business.save()
            for img in request.FILES.getlist('images'):
                BusinessImage.objects.create(business=business, image=img)
            save_dynamic_fields(request, business)

            # Send notifications to vendor and admins
            try:
                from django.contrib.auth import get_user_model
                from apps.notifications.tasks import send_notification_task
                
                User = get_user_model()
                
                # Notify Vendor
                send_notification_task(
                    user_id=request.user.id,
                    title="Business Listing Submitted",
                    message=f"Successfully added business '{business.company_name}'. Pending admin approval.",
                    channels=["database", "push"],
                )
                
                # Notify Admins
                for admin in User.objects.filter(is_superuser=True):
                    send_notification_task(
                        user_id=admin.id,
                        title="New Business Pending Approval",
                        message=f"Business listing '{business.company_name}' found. Please approve or reject it.",
                        channels=["database", "push"],
                    )
            except Exception:
                pass

            messages.success(request, 'Business submitted successfully. Pending admin approval.')
            return redirect('vendors:vendor.dashboard')

        submitted_values = {k: v for k, v in request.POST.items() if k.startswith('field_')}
        return render(request, 'vendors/add_business.html', {
            'form': form,
            'categories_with_fields': get_categories_with_fields(),
            'submitted_values': submitted_values,
            'active_tab': 'add_business',
        })


class VendorViewBusinessView(LoginRequiredMixin, View):
    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk, user=request.user)
        field_values = BusinessFieldValue.objects.select_related('field').filter(business=business)
        parsed_field_values = []
        for fv in field_values:
            value = fv.value
            if fv.field.field_type == 'checkbox' and value:
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    value = [value]
            parsed_field_values.append({
                'label': fv.field.label,
                'field_type': fv.field.field_type,
                'value': value,
            })
        
        # Get active listing plan subscription
        listing_subscription = (
            BusinessListingSubscription.objects
            .filter(business=business, is_active=True, payment_status='SUCCESS')
            .order_by('-created_at')
            .first()
        )
        if listing_subscription and not listing_subscription.subscription_active:
            listing_subscription = None

        return render(request, 'vendors/view_business.html', {
            'business': business,
            'field_values': parsed_field_values,
            'listing_subscription': listing_subscription,
            'active_tab': 'my_businesses',
        })

class VendorEditBusinessView(LoginRequiredMixin, View):

    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk, user=request.user)
        form = BusinessForm(instance=business)
        existing_values = {
            fv.field_id: fv.value if fv.value is not None else ''
            for fv in BusinessFieldValue.objects.filter(business=business)
        }
        return render(request, 'vendors/edit_business.html', {
            'form': form,
            'business': business,
            'categories_with_fields': get_categories_with_fields(),
            'existing_values': existing_values,
            'active_tab': 'my_businesses',
        })

    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk, user=request.user)  # ← correct
        form = BusinessForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            for img in request.FILES.getlist('images'):
                BusinessImage.objects.create(business=business, image=img)
            save_dynamic_fields(request, business)
            messages.success(request, 'Business updated successfully.')
            return redirect('vendors:vendor.dashboard')

        existing_values = {
            fv.field_id: fv.value if fv.value is not None else ''
            for fv in BusinessFieldValue.objects.filter(business=business)
        }
        return render(request, 'vendors/edit_business.html', {
            'form': form,
            'business': business,
            'categories_with_fields': get_categories_with_fields(),
            'existing_values': existing_values,
            'active_tab': 'my_businesses',
        })





class VendorImageDeleteView(LoginRequiredMixin, View):

    def get(self, request, pk):
        img = get_object_or_404(BusinessImage, pk=pk)
        business_pk = img.business.pk
        img.delete()
        return redirect('vendors:edit_business', pk=business_pk)
    


# reviews

class VendorReviewListView(LoginRequiredMixin, ListView):
    model = Review
    template_name = "vendors/vendor_reviews.html"
    context_object_name = "reviews"
    paginate_by = 5

    def get_queryset(self):
        queryset = (
            Review.objects.filter(
                business__user=self.request.user
            )
            .select_related(
                "user",
                "business"
            )
            .order_by("-created_at")
        )

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        rating = self.request.GET.get("rating")
        business = self.request.GET.get("business")
        from_date = self.request.GET.get("from_date")
        to_date = self.request.GET.get("to_date")
        sort = self.request.GET.get("sort")

        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search)
                | Q(review__icontains=search)
                | Q(business__company_name__icontains=search)  # Changed from business_name to company_name
            )

        if status:
            queryset = queryset.filter(
                status=status
            )

        if rating:
            queryset = queryset.filter(
                rating=rating
            )

        if business:
            queryset = queryset.filter(
                business_id=business
            )

        if from_date:
            queryset = queryset.filter(
                created_at__date__gte=from_date
            )

        if to_date:
            queryset = queryset.filter(
                created_at__date__lte=to_date
            )

        if sort == "oldest":
            queryset = queryset.order_by("created_at")
        elif sort == "highest_rating":
            queryset = queryset.order_by("-rating")
        elif sort == "lowest_rating":
            queryset = queryset.order_by("rating")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        reviews = Review.objects.filter(
            business__user=self.request.user
        )

        context["total_reviews"] = reviews.count()
        context["pending_reviews"] = reviews.filter(status="pending").count()
        context["approved_reviews"] = reviews.filter(status="approved").count()
        context["rejected_reviews"] = reviews.filter(status="rejected").count()

        # FIXED: Changed 'review__rating' to 'reviews__rating' based on your model definition
        context["businesses"] = self.request.user.businesses.all().annotate(
            average_rating=Avg('reviews__rating')
        )

        # Retain active search configurations inside the UI fields
        context["selected_business"] = self.request.GET.get("business", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_rating"] = self.request.GET.get("rating", "")
        context["selected_sort"] = self.request.GET.get("sort", "")
        context["search_query"] = self.request.GET.get("search", "")
        context["from_date"] = self.request.GET.get("from_date", "")
        context["to_date"] = self.request.GET.get("to_date", "")

        return context


@login_required
def approve_review(request, pk):

    review = get_object_or_404(
        Review,
        pk=pk,
        business__user=request.user
    )

    review.status = "approved"
    review.vendor_verified = True
    review.approved_at = timezone.now()

    review.save()
    if review.user:
        try:
            from apps.notifications.tasks import send_notification_task
            send_notification_task(
                user_id=review.user.id,
                title="Review Published",
                message=f"🎉 Your review for '{review.business.company_name}' has been verified and published!",
                channels=["database", "push"]
            )
        except Exception:
            pass

    return redirect("vendors:vendor_reviews")

@login_required
def reject_review(request, pk):

    review = get_object_or_404(
        Review,
        pk=pk,
        business__user=request.user
    )

    review.status = "rejected"

    review.save()

    return redirect("vendors:vendor_reviews")


# ─────────────────────────────────────────────────────────────────
# Business Listing Plans  –  Contact-unlock plan purchase flow
# ─────────────────────────────────────────────────────────────────

class VendorListingPlansView(LoginRequiredMixin, View):
    """Show all active listing plans for a specific business the vendor owns."""

    def get(self, request, business_pk):
        business = get_object_or_404(Business, pk=business_pk, user=request.user)

        plans = BusinessListingPlan.objects.filter(is_active=True)

        # Get the most recent active subscription for this business
        active_subscription = (
            BusinessListingSubscription.objects
            .filter(business=business, is_active=True, payment_status='SUCCESS')
            .order_by('-created_at')
            .first()
        )

        # Auto-expire if needed
        if active_subscription and not active_subscription.subscription_active:
            active_subscription = None

        return render(request, 'vendors/listing_plans.html', {
            'business': business,
            'plans': plans,
            'active_subscription': active_subscription,
            'active_tab': 'my_businesses',
        })


class VendorPurchaseListingPlanView(LoginRequiredMixin, View):
    """Initiate Razorpay payment for a business listing plan."""

    def get(self, request, business_pk, plan_pk):
        business = get_object_or_404(Business, pk=business_pk, user=request.user)
        plan = get_object_or_404(BusinessListingPlan, pk=plan_pk, is_active=True)

        amount_in_paise = int(plan.price * 100)

        try:
            razorpay_order = razorpay_client.order.create(data={
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1',
            })

            # Create a PENDING subscription record
            BusinessListingSubscription.objects.create(
                business=business,
                plan=plan,
                vendor=request.user,
                razorpay_order_id=razorpay_order['id'],
                amount=plan.price,
                payment_status='PENDING',
                is_active=False,
            )

            context = {
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': django_settings.RAZORPAY_KEY_ID,
                'amount': amount_in_paise,
                'currency': 'INR',
                'plan': plan,
                'business': business,
                'user_email': request.user.email,
                'user_phone': getattr(request.user, 'phone', '') or '',
                'user_name': (
                    f"{request.user.first_name} {request.user.last_name}".strip()
                    or request.user.email
                ),
            }
            return render(request, 'vendors/listing_plan_checkout.html', context)

        except Exception as e:
            messages.error(request, f"Failed to initialize payment: {str(e)}")
            return redirect('vendors:listing_plans', business_pk=business_pk)


@method_decorator(csrf_exempt, name='dispatch')
class VendorVerifyListingPlanPaymentView(LoginRequiredMixin, View):
    """Verify Razorpay signature and activate the subscription."""

    def post(self, request):
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')
        error_code = request.POST.get('error[code]', None)
        business_pk = request.POST.get('business_pk', '')

        if error_code or not razorpay_payment_id:
            error_order_id = request.POST.get('error[metadata][order_id]', '')
            if error_order_id:
                sub = BusinessListingSubscription.objects.filter(
                    razorpay_order_id=error_order_id, vendor=request.user
                ).first()
                if sub:
                    sub.payment_status = 'FAILED'
                    sub.save()
                    try:
                        from apps.notifications.tasks import send_notification_task
                        send_notification_task(
                            user_id=request.user.id,
                            title="Listing Plan Payment Failed",
                            message=f"Your payment for the '{sub.plan.name}' listing plan has failed.",
                            channels=["database", "push"]
                        )
                    except Exception:
                        pass
            messages.error(request, 'Payment failed or was cancelled.')
            if business_pk:
                return redirect('vendors:listing_plans', business_pk=business_pk)
            return redirect('vendors:my_businesses')

        subscription = get_object_or_404(
            BusinessListingSubscription,
            razorpay_order_id=razorpay_order_id,
            vendor=request.user,
        )

        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Activate the subscription
            now = timezone.now()
            subscription.razorpay_payment_id = razorpay_payment_id
            subscription.razorpay_signature = razorpay_signature
            subscription.payment_status = 'SUCCESS'
            subscription.is_active = True
            
            # Stacking/Extension check: if there is an active subscription running, start this new one when it ends
            existing_active_sub = BusinessListingSubscription.objects.filter(
                business=subscription.business,
                is_active=True,
                payment_status='SUCCESS',
                end_date__gt=now
            ).order_by('-end_date').first()
            
            if existing_active_sub:
                subscription.start_date = existing_active_sub.end_date
            else:
                subscription.start_date = now

            subscription.end_date = subscription.start_date + __import__('datetime').timedelta(
                days=subscription.plan.validity_days
            )
            subscription.save()
            try:
                from apps.notifications.tasks import send_notification_task
                send_notification_task(
                    user_id=request.user.id,
                    title="Listing Plan Activated",
                    message=f"🎉 Successfully purchased '{subscription.plan.name}' listing plan for business '{subscription.business.company_name}'. Active until {subscription.end_date.strftime('%d %b %Y')}.",
                    channels=["database", "push"]
                )
            except Exception:
                pass

            messages.success(
                request,
                f'🎉 "{subscription.plan.name}" plan activated! '
                f'Clients can now see your contact details until '
                f'{subscription.end_date.strftime("%d %b %Y")}.'
            )
            return redirect('vendors:view_business', pk=subscription.business.pk)

        except razorpay.errors.SignatureVerificationError:
            subscription.payment_status = 'FAILED'
            subscription.save()
            try:
                from apps.notifications.tasks import send_notification_task
                send_notification_task(
                    user_id=request.user.id,
                    title="Listing Plan Payment Failed",
                    message=f"Your signature verification for the '{subscription.plan.name}' listing plan has failed.",
                    channels=["database", "push"]
                )
            except Exception:
                pass
            messages.error(request, 'Payment verification failed. Signature mismatch.')
            return redirect('vendors:listing_plans', business_pk=subscription.business.pk)


class VendorAllListingPlansView(LoginRequiredMixin, View):
    """
    Shows all the vendor's businesses and their current listing plan status,
    with a link to buy or renew.
    """
    def get(self, request):
        businesses = Business.objects.filter(user=request.user)
        businesses_with_plans = []
        for b in businesses:
            sub = (
                BusinessListingSubscription.objects
                .filter(business=b, is_active=True, payment_status='SUCCESS')
                .order_by('-created_at')
                .first()
            )
            if sub and not sub.subscription_active:
                sub = None
            businesses_with_plans.append({
                'business': b,
                'active_subscription': sub
            })
        return render(request, 'vendors/all_listing_plans.html', {
            'businesses_with_plans': businesses_with_plans,
            'active_tab': 'listing_plans',
        })
# vendor profile updated

class VendorProfileView(LoginRequiredMixin, View):

    template_name = "accounts/vendor/vendor_profile_update.html"

    def get(self, request):

        return render(
            request,
            self.template_name,
            {
                "user_obj": request.user
            }
        )

    def post(self, request):

        user = request.user

        user.first_name = request.POST.get(
            "first_name",
            user.first_name
        )

        user.last_name = request.POST.get(
            "last_name",
            user.last_name
        )

        if request.FILES.get("profile_image"):

            user.profile_image = request.FILES.get(
                "profile_image"
            )

        current_password = request.POST.get(
            "current_password",
            ""
        ).strip()

        new_password = request.POST.get(
            "new_password",
            ""
        ).strip()

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        ).strip()

        if current_password or new_password or confirm_password:

            if not user.check_password(current_password):

                messages.error(
                    request,
                    "Current password is incorrect."
                )

                return redirect("vendors:vendor_profile")

            if new_password != confirm_password:

                messages.error(
                    request,
                    "Passwords do not match."
                )

                return redirect("vendors:vendor_profile")

            user.set_password(new_password)

            user.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "Password changed successfully."
            )

            return redirect("vendors:vendor_profile")

        user.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("vendors:vendor_profile")
    
class VendorPaymentHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        qs = (
            BusinessListingSubscription.objects
            .filter(vendor=request.user)
            .select_related('plan', 'business')
            .order_by('-created_at')
        )
        payments = paginate_queryset(request, qs, per_page=10)
        return render(request, 'vendors/payment_history.html', {
            'payments': payments,
            'page_obj': payments,
            'active_tab': 'payment_history',
        })


