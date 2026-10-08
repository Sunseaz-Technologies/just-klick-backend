from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import razorpay
from apps.dynamic.pagination import paginate_queryset
from .models import (
    AdvertisementPlan,
    VendorAdvertisementSubscription,
    Advertisement,
    AdvertisementPayment,
    AdvertisementPlanFeature
)
import csv
from django.http import HttpResponse
from django.db.models import Q, Sum
from apps.accounts.models import User
from apps.accounts.decorators import superadmin_required
import collections
from datetime import timedelta

razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class AdvertisementPlanListView(View):

    def get(self, request):

        plans = AdvertisementPlan.objects.filter(is_active=True)

        return render(request, "advertisements/plans.html", {"plans": plans})


class PurchasePlanView(View):

    def get(self, request, pk):

        plan = get_object_or_404(AdvertisementPlan, pk=pk)

        # Check active subscription
        active_subscription = VendorAdvertisementSubscription.objects.filter(
            vendor=request.user, is_active=True
        ).first()

        if (
            active_subscription
            and active_subscription.start_date
            and active_subscription.subscription_active
        ):

            messages.warning(request, "You already have an active plan.")

            return redirect("advertisements:my_ads")

        amount_in_paise = int(plan.price * 100)

        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1",
        }

        try:

            razorpay_order = razorpay_client.order.create(data=order_data)

            AdvertisementPayment.objects.create(
                vendor=request.user,
                plan=plan,
                razorpay_order_id=razorpay_order["id"],
                amount=plan.price,
                status="PENDING",
            )

            context = {
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": amount_in_paise,
                "currency": "INR",
                "plan": plan,
                "user_email": request.user.email,
                "user_phone": request.user.phone or "",
                "user_name": f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.email,
            }

            return render(request, "advertisements/razorpay_checkout.html", context)

        except Exception as e:

            messages.error(request, f"Failed to initialize payment: {str(e)}")

            return redirect("advertisements:plans")


@method_decorator(csrf_exempt, name="dispatch")
class VerifyPaymentView(View):
    def post(self, request):
        razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
        razorpay_order_id = request.POST.get("razorpay_order_id", "")
        razorpay_signature = request.POST.get("razorpay_signature", "")
        error_code = request.POST.get("error[code]", None)

        # If there's an error from Razorpay
        if error_code or not razorpay_payment_id:
            error_order_id = request.POST.get("error[metadata][order_id]", "")
            if error_order_id:
                payment = AdvertisementPayment.objects.filter(
                    razorpay_order_id=error_order_id, vendor=request.user
                ).first()
                if payment:
                    payment.status = "FAILED"
                    payment.save()
                    try:
                        from apps.notifications.tasks import send_notification_task

                        send_notification_task(
                            user_id=request.user.id,
                            title="Ad Plan Payment Failed",
                            message=f"Your payment for the '{payment.plan.name}' advertisement plan has failed.",
                            channels=["database", "push"],
                        )
                    except Exception:
                        pass
            messages.error(request, "Payment failed or was cancelled.")
            return redirect("advertisements:plans")

        payment = get_object_or_404(
            AdvertisementPayment,
            razorpay_order_id=razorpay_order_id,
            vendor=request.user,
        )

        try:
            razorpay_client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )

            payment.status = "SUCCESS"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

            VendorAdvertisementSubscription.objects.create(
                vendor=request.user, plan=payment.plan, start_date=None, end_date=None
            )
            try:
                from apps.notifications.tasks import send_notification_task

                send_notification_task(
                    user_id=request.user.id,
                    title="Ad Plan Purchased",
                    message=f"🎉 Successfully purchased '{payment.plan.name}' advertisement plan. Go to 'Add Advertisement' to activate it.",
                    channels=["database", "push"],
                )
            except Exception:
                pass

            messages.success(request, "Plan purchased successfully.")
            return redirect("advertisements:my_ads")

        except razorpay.errors.SignatureVerificationError:
            payment.status = "FAILED"
            payment.save()
            try:
                from apps.notifications.tasks import send_notification_task

                send_notification_task(
                    user_id=request.user.id,
                    title="Ad Plan Payment Failed",
                    message=f"Your signature verification for the '{payment.plan.name}' advertisement plan has failed.",
                    channels=["database", "push"],
                )
            except Exception:
                pass
            messages.error(request, "Payment verification failed. Signature mismatch.")
            return redirect("advertisements:plans")


class AddAdvertisementView(View):

    def get(self, request):

        subscription = (
            VendorAdvertisementSubscription.objects.filter(
                vendor=request.user, is_active=True
            )
            .order_by("-id")
            .first()
        )

        if not subscription:

            messages.error(request, "Please purchase a plan first.")

            return redirect("advertisements:plans")

        return render(request, "advertisements/add_advertisement.html")

    def post(self, request):

        subscription = (
            VendorAdvertisementSubscription.objects.filter(
                vendor=request.user, is_active=True
            )
            .order_by("-id")
            .first()
        )

        if not subscription:

            messages.error(request, "Purchase a plan first.")

            return redirect("advertisements:plans")

        # START TIMER ONLY ON FIRST AD

        if subscription.start_date is None:

            subscription.activate_subscription()

        Advertisement.objects.create(
            vendor=request.user,
            subscription=subscription,
            image=request.FILES.get("image"),
            redirect_url=request.POST.get("redirect_url"),
        )

        messages.success(request, "Advertisement added successfully.")

        return redirect("advertisements:my_ads")


class EditAdvertisementView(View):

    def get(self, request, pk):

        advertisement = get_object_or_404(Advertisement, pk=pk, vendor=request.user)

        return render(
            request,
            "advertisements/edit_advertisement.html",
            {"advertisement": advertisement},
        )

    def post(self, request, pk):

        advertisement = get_object_or_404(Advertisement, pk=pk, vendor=request.user)

        advertisement.redirect_url = request.POST.get("redirect_url")

        if request.FILES.get("image"):

            advertisement.image = request.FILES.get("image")

        advertisement.save()

        messages.success(request, "Advertisement updated successfully.")

        return redirect("advertisements:my_ads")


class MyAdvertisementsView(View):

    def get(self, request):

        ads = Advertisement.objects.filter(vendor=request.user)

        subscription = (
            VendorAdvertisementSubscription.objects.filter(vendor=request.user)
            .select_related("plan")
            .order_by("-id")
            .first()
        )

        is_plan_active = False
        remaining_days = None

        if subscription:
            is_plan_active = subscription.subscription_active

            if subscription.start_date and subscription.end_date:
                remaining_days = max(0, (subscription.end_date - timezone.now()).days)

        return render(
            request,
            "advertisements/my_ads.html",
            {
                "ads": ads,
                "subscription": subscription,
                "remaining_days": remaining_days,
                "is_plan_active": is_plan_active,
            },
        )


# list creating and editing deleeting advertisemnts in admin
class AdvertisementPlanAdminListView(View):

    def get(self, request):

        plans_queryset = AdvertisementPlan.objects.all().order_by("-id")

        plans = paginate_queryset(request, plans_queryset, per_page=1)

        context = {
            "plans": plans,
            "page_obj": plans,
            "active_tab": "advertisement_plans",
        }

        return render(
            request,
            "advertisements/admin_plan_list.html",
            context,
        )


class AdvertisementPlanCreateView(View):

    def get(self, request):

        return render(
            request,
            "advertisements/admin_plan_form.html",
            {"active_tab": "advertisement_plans"},
        )

    def post(self, request):

        plan = AdvertisementPlan.objects.create(
            name=request.POST.get("name"),
            price=request.POST.get("price"),
            validity_days=request.POST.get("validity_days"),
            is_active=True,
        )

        # Get all feature inputs
        features = request.POST.getlist("features")

        for feature in features:
            feature = feature.strip()
            if feature:
                AdvertisementPlanFeature.objects.create(
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
                    title="New Ad Plan Created!",
                    message="Explore our ads",
                    channels=["database", "push"]
                )
        except Exception:
            pass

        messages.success(request, "Plan created successfully.")

        return redirect("advertisements:admin_plan_list")


class AdvertisementPlanEditView(View):

    def get(self, request, pk):

        plan = get_object_or_404(AdvertisementPlan, pk=pk)

        return render(
            request,
            "advertisements/admin_plan_form.html",
            {"plan": plan, "active_tab": "advertisement_plans"},
        )

    def post(self, request, pk):

        plan = get_object_or_404(AdvertisementPlan, pk=pk)

        plan.name = request.POST.get("name")
        plan.price = request.POST.get("price")
        plan.validity_days = request.POST.get("validity_days")

        plan.save()

        # Get all feature inputs
        features = request.POST.getlist("features")

        # Replace old features with the submitted list
        plan.features.all().delete()
        for feature in features:
            feature = feature.strip()
            if feature:
                AdvertisementPlanFeature.objects.create(
                    plan=plan,
                    feature=feature
                )

        messages.success(request, "Plan updated successfully.")

        return redirect("advertisements:admin_plan_list")

class AdvertisementPlanDeleteView(View):

    def get(self, request, pk):

        plan = get_object_or_404(AdvertisementPlan, pk=pk)

        return render(request, "advertisements/plan_delete.html", {"plan": plan})

    def post(self, request, pk):

        plan = get_object_or_404(AdvertisementPlan, pk=pk)

        plan.delete()

        messages.success(request, "Plan deleted successfully.")

        return redirect("advertisements:admin_plan_list")


class AdvertisementEditView(View):

    def get(self, request, pk):

        ad = get_object_or_404(Advertisement, pk=pk, vendor=request.user)

        return render(request, "advertisements/edit_advertisement.html", {"ad": ad})

    def post(self, request, pk):

        ad = get_object_or_404(Advertisement, pk=pk, vendor=request.user)

        ad.redirect_url = request.POST.get("redirect_url")

        image = request.FILES.get("image")

        if image:
            ad.image = image

        ad.save()

        messages.success(request, "Advertisement updated successfully.")

        return redirect("advertisements:my_ads")


class AdvertisementDeleteView(View):

    def get(self, request, pk):

        ad = get_object_or_404(Advertisement, pk=pk, vendor=request.user)

        ad.delete()

        messages.success(request, "Advertisement deleted successfully.")

        return redirect("advertisements:my_ads")


class PaymentHistoryView(View):

    def get(self, request):

        payments_queryset = (
            AdvertisementPayment.objects.filter(vendor=request.user)
            .select_related("plan", "vendor")
            .order_by("-created_at")
        )

        payments = paginate_queryset(request, payments_queryset, per_page=5)

        return render(
            request,
            "advertisements/payment_history.html",
            {
                "payments": payments,
                "page_obj": payments,
            },
        )


class AdvertisementPaymentAdminListView(View):

    def get(self, request):

        payments_queryset = AdvertisementPayment.objects.select_related(
            "vendor", "plan"
        ).order_by("-created_at")

        total_amount = sum(
            payment.amount for payment in payments_queryset.filter(status="SUCCESS")
        )
        total_transactions = payments_queryset.count()

        payments = paginate_queryset(request, payments_queryset, per_page=5)

        context = {
            "payments": payments,
            "page_obj": payments,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "active_tab": "advertisement_payments",
        }

        return render(
            request,
            "advertisements/admin_payment_list.html",
            context,
        )


class AdvertisementPaymentExportCSVView(View):

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="advertisement_payments.csv"'
        )

        writer = csv.writer(response)

        # Header Row
        writer.writerow(
            [
                "S.No",
                "Vendor Name",
                "Email",
                "Phone",
                "Plan",
                "Amount",
                "Order ID",
                "Payment ID",
                "Status",
                "Date",
            ]
        )

        payments = AdvertisementPayment.objects.select_related(
            "vendor", "plan"
        ).order_by("-created_at")

        for index, payment in enumerate(payments, start=1):
            writer.writerow(
                [
                    index,
                    payment.vendor.get_full_name() if payment.vendor else "N/A",
                    payment.vendor.email if payment.vendor else "",
                    payment.vendor.phone if payment.vendor else "",
                    payment.plan.name if payment.plan else "",
                    payment.amount,
                    payment.razorpay_order_id,
                    payment.razorpay_payment_id or "-",
                    payment.status,
                    payment.created_at.strftime("%d %b %Y %I:%M %p"),
                ]
            )

        return response


@method_decorator(superadmin_required, name="dispatch")
class AdvertisementAdminDashboardView(View):
    def get(self, request):
        now = timezone.now()

        # Totals
        total_vendors = User.objects.filter(role__name__iexact="Vendor").count()
        total_advertisements = Advertisement.objects.count()
        total_orders = AdvertisementPayment.objects.count()

        total_revenue = (
            AdvertisementPayment.objects.filter(status="SUCCESS").aggregate(
                Sum("amount")
            )["amount__sum"]
            or 0.00
        )

        successful_payments = AdvertisementPayment.objects.filter(
            status="SUCCESS"
        ).count()
        pending_payments = AdvertisementPayment.objects.filter(status="PENDING").count()
        failed_payments = AdvertisementPayment.objects.filter(status="FAILED").count()

        active_subscriptions = (
            VendorAdvertisementSubscription.objects.filter(
                is_active=True,
                start_date__isnull=False,
                end_date__gt=now
            )
            .count()
        )

        expired_subscriptions = VendorAdvertisementSubscription.objects.filter(
            Q(is_active=False) | Q(end_date__lte=now)
        ).count()


        # Chronological last 6 months lists
        months_list = []
        for i in range(5, -1, -1):
            d = now - timedelta(days=i * 30)
            months_list.append(d.strftime("%b %Y"))

        # Group by months using python logic for db agnosticism
        six_months_ago = now - timedelta(days=180)
        recent_payments = AdvertisementPayment.objects.filter(
            status="SUCCESS", created_at__gte=six_months_ago
        )
        recent_subs = VendorAdvertisementSubscription.objects.filter(
            start_date__gte=six_months_ago
        )

        revenue_map = collections.defaultdict(float)
        for p in recent_payments:
            month_key = p.created_at.strftime("%b %Y")
            revenue_map[month_key] += float(p.amount)

        subs_map = collections.defaultdict(int)
        for s in recent_subs:
            if s.start_date:
                month_key = s.start_date.strftime("%b %Y")
                subs_map[month_key] += 1

        revenue_chart_data = [revenue_map[m] for m in months_list]
        subs_chart_data = [subs_map[m] for m in months_list]

        # Recent activities
        recent_activities = []
        for p in AdvertisementPayment.objects.select_related("vendor", "plan").order_by(
            "-created_at"
        )[:5]:
            recent_activities.append(
                {
                    "title": f"Payment of ₹{p.amount} received",
                    "detail": f"Vendor: {p.vendor.email} | Plan: {p.plan.name}",
                    "timestamp": p.created_at,
                    "badge_class": (
                        "bg-success"
                        if p.status == "SUCCESS"
                        else (
                            "bg-warning text-dark"
                            if p.status == "PENDING"
                            else "bg-danger"
                        )
                    ),
                    "badge_text": p.status,
                    "icon": "bi-credit-card",
                }
            )
        for s in (
            VendorAdvertisementSubscription.objects.select_related("vendor", "plan")
            .filter(start_date__isnull=False)
            .order_by("-start_date")[:5]
        ):
            recent_activities.append(
                {
                    "title": f"Subscription Activated",
                    "detail": f"Vendor: {s.vendor.email} | Plan: {s.plan.name}",
                    "timestamp": s.start_date,
                    "badge_class": "bg-primary" if s.is_active else "bg-secondary",
                    "badge_text": "Active" if s.subscription_active else "Expired",
                    "icon": "bi-megaphone",
                }
            )
        for a in Advertisement.objects.select_related("vendor").order_by("-created_at")[
            :5
        ]:
            recent_activities.append(
                {
                    "title": "New Ad Uploaded",
                    "detail": f"Vendor: {a.vendor.email} | Redirect: {a.redirect_url}",
                    "timestamp": a.created_at,
                    "badge_class": "bg-info text-dark",
                    "badge_text": "Ad Banner",
                    "icon": "bi-image",
                }
            )
        recent_activities = sorted(
            recent_activities, key=lambda x: x["timestamp"], reverse=True
        )[:8]

        # Latest Payments
        latest_payments_qs = AdvertisementPayment.objects.select_related(
            "vendor", "plan"
        ).order_by("-created_at")[:5]

        # Decorate latest payments with subscription status
        vendor_ids = [p.vendor_id for p in latest_payments_qs]
        plan_ids = [p.plan_id for p in latest_payments_qs]
        subs_queryset = VendorAdvertisementSubscription.objects.filter(
            vendor_id__in=vendor_ids, plan_id__in=plan_ids
        ).order_by("-id")
        
        subs_by_vendor_plan = collections.defaultdict(list)
        for sub in subs_queryset:
            subs_by_vendor_plan[(sub.vendor_id, sub.plan_id)].append(sub)

        success_db_payments = AdvertisementPayment.objects.filter(
            vendor_id__in=vendor_ids,
            plan_id__in=plan_ids,
            status="SUCCESS"
        ).order_by("-id")
        
        payments_by_vendor_plan = collections.defaultdict(list)
        for p in success_db_payments:
            payments_by_vendor_plan[(p.vendor_id, p.plan_id)].append(p)

        latest_payments_with_subs = []
        for p in latest_payments_qs:
            sub = None
            sub_status = "No Subscription"
            if p.status == "SUCCESS":
                key = (p.vendor_id, p.plan_id)
                p_list = payments_by_vendor_plan[key]
                sub_list = subs_by_vendor_plan[key]
                try:
                    idx = p_list.index(p)
                    if idx < len(sub_list):
                        sub = sub_list[idx]
                except ValueError:
                    pass

            if sub:
                if not sub.start_date:
                    sub_status = "Pending Activation"
                else:
                    sub_status = "Active" if sub.subscription_active else "Expired"
            latest_payments_with_subs.append(
                {"payment": p, "subscription_status": sub_status, "subscription": sub}
            )


        context = {
            "total_vendors": total_vendors,
            "total_advertisements": total_advertisements,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "successful_payments": successful_payments,
            "pending_payments": pending_payments,
            "failed_payments": failed_payments,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "months_list": months_list,
            "revenue_chart_data": revenue_chart_data,
            "subs_chart_data": subs_chart_data,
            "recent_activities": recent_activities,
            "latest_payments_with_subs": latest_payments_with_subs,
            "active_tab": "advertisement_dashboard",
        }
        return render(request, "advertisements/dashboard.html", context)


@method_decorator(superadmin_required, name="dispatch")
class AdvertisementOrderListView(View):
    def get(self, request):
        search_query = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status", "").strip()
        sub_filter = request.GET.get("subscription_status", "").strip()

        payments_queryset = AdvertisementPayment.objects.select_related(
            "vendor", "plan"
        ).order_by("-created_at")

        if search_query:
            payments_queryset = payments_queryset.filter(
                Q(vendor__email__icontains=search_query)
                | Q(vendor__username__icontains=search_query)
                | Q(razorpay_order_id__icontains=search_query)
                | Q(razorpay_payment_id__icontains=search_query)
                | Q(plan__name__icontains=search_query)
            )

        if status_filter:
            payments_queryset = payments_queryset.filter(status=status_filter)

        if sub_filter:
            now = timezone.now()
            if sub_filter == "ACTIVE":
                active_vendors = (
                    VendorAdvertisementSubscription.objects.filter(is_active=True)
                    .filter(Q(end_date__gt=now) | Q(end_date__isnull=True))
                    .values_list("vendor_id", flat=True)
                )
                payments_queryset = payments_queryset.filter(
                    vendor_id__in=active_vendors
                )
            elif sub_filter == "EXPIRED":
                expired_vendors = VendorAdvertisementSubscription.objects.filter(
                    Q(is_active=False) | Q(end_date__lte=now)
                ).values_list("vendor_id", flat=True)
                payments_queryset = payments_queryset.filter(
                    vendor_id__in=expired_vendors
                )

        # Total counts
        total_count = payments_queryset.count()

        # Paginate
        page_obj = paginate_queryset(request, payments_queryset, per_page=10)

        # Build subscription map for page payments
        vendor_ids = [p.vendor_id for p in page_obj]
        plan_ids = [p.plan_id for p in page_obj]

        subs_queryset = VendorAdvertisementSubscription.objects.filter(
            vendor_id__in=vendor_ids, plan_id__in=plan_ids
        )

        latest_subs = {}
        for sub in subs_queryset:
            latest_subs[(sub.vendor_id, sub.plan_id)] = sub

        # Decorate page payment items with subscription status
        payments_with_subs = []
        for p in page_obj:
            sub = latest_subs.get((p.vendor_id, p.plan_id))
            sub_status = "No Subscription"
            days_left = None
            if sub:
                if sub.subscription_active:
                    sub_status = "Active"
                else:
                    sub_status = "Expired"
                if sub.start_date and sub.end_date:
                    days_left = max(0, (sub.end_date - timezone.now()).days)
            payments_with_subs.append(
                {
                    "payment": p,
                    "subscription_status": sub_status,
                    "days_remaining": days_left,
                    "subscription": sub,
                }
            )

        context = {
            "payments_with_subs": payments_with_subs,
            "page_obj": page_obj,
            "search": search_query,
            "status_filter": status_filter,
            "sub_filter": sub_filter,
            "total_count": total_count,
            "active_tab": "advertisement_orders",
        }
        return render(request, "advertisements/orders.html", context)


@method_decorator(superadmin_required, name="dispatch")
class AdvertisementOrderDetailView(View):
    def get(self, request, pk):
        payment = get_object_or_404(
            AdvertisementPayment.objects.select_related("vendor", "plan"), pk=pk
        )

        # Find matching subscription
        subscription = (
            VendorAdvertisementSubscription.objects.filter(
                vendor=payment.vendor, plan=payment.plan
            )
            .order_by("-id")
            .first()
        )

        # Find advertisements uploaded by this vendor under this subscription
        advertisement = None
        if subscription:
            advertisement = (
                Advertisement.objects.filter(
                    vendor=payment.vendor, subscription=subscription
                )
                .order_by("-created_at")
                .first()
            )

        remaining_days = None
        is_subscription_active = False
        if subscription:
            is_subscription_active = subscription.subscription_active
            if subscription.start_date and subscription.end_date:
                remaining_days = max(0, (subscription.end_date - timezone.now()).days)

        context = {
            "payment": payment,
            "subscription": subscription,
            "advertisement": advertisement,
            "remaining_days": remaining_days,
            "is_subscription_active": is_subscription_active,
            "active_tab": "advertisement_orders",
        }
        return render(request, "advertisements/order_detail.html", context)
