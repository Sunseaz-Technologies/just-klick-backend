from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.core.files.storage import FileSystemStorage
from .models import AboutSection,WhyChooseUss,FAQ,ServiceSection,PromiseSection,PromiseCard,BulkPartnerSection,PartnerImage,WhoWeAreSection,Counter,PopularService,ValueItem,TeamSection,ContactPage,ContactFeature,ContactFormField,ContactEnquiry,TouristPlace,PopularSearch,PopularBusinessSearch
import json
from apps.dynamic.pagination import paginate_queryset
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.dateparse import parse_date
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import TermsAndConditions, PrivacyPolicy

class WhyChooseUsListViews(View):

    def get(self, request):

        items_queryset = WhyChooseUss.objects.all().order_by("-id")

        items = paginate_queryset(request, items_queryset, per_page=10)

        return render(
            request,
            "dynamic/whychooseus/list.html",
            {
                "items": items,
                "page_obj": items,
                "active_tab": "why_choose_us",
            },
        )


class WhyChooseUsCreateViews(View):

    def get(self, request):

        return render(
            request, "dynamic/whychooseus/create.html", {"active_tab": "why_choose_us"}
        )

    def post(self, request):

        WhyChooseUss.objects.create(
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            icon=request.FILES.get("icon"),
            is_active=bool(request.POST.get("is_active")),
        )

        messages.success(request, "Why Choose Us item created successfully.")

        return redirect("dynamic:why_list")


class WhyChooseUsUpdateViews(View):

    def get(self, request, pk):

        item = get_object_or_404(WhyChooseUss, pk=pk)

        return render(
            request,
            "dynamic/whychooseus/update.html",
            {"item": item, "active_tab": "why_choose_us"},
        )

    def post(self, request, pk):

        item = get_object_or_404(WhyChooseUss, pk=pk)

        item.title = request.POST.get("title")
        item.description = request.POST.get("description")
        item.is_active = bool(request.POST.get("is_active"))

        icon = request.FILES.get("icon")

        if icon:
            item.icon = icon

        item.save()

        messages.success(request, "Why Choose Us item updated successfully.")

        return redirect("dynamic:why_list")


class WhyChooseUsDeleteViews(View):

    def post(self, request, pk):

        item = get_object_or_404(WhyChooseUss, pk=pk)

        item.delete()

        messages.success(request, "Why Choose Us item deleted successfully.")

        return redirect("dynamic:why_list")


class FAQListView(View):

    def get(self, request):

        items_queryset = FAQ.objects.all().order_by("-id")

        items = paginate_queryset(request, items_queryset, per_page=10)

        return render(
            request,
            "dynamic/faq/list.html",
            {
                "items": items,
                "page_obj": items,
                "active_tab": "faq",
            },
        )


class FAQCreateView(View):

    def get(self, request):

        return render(request, "dynamic/faq/create.html", {"active_tab": "faq"})

    def post(self, request):

        FAQ.objects.create(
            question=request.POST.get("question"),
            answer=request.POST.get("answer"),
            is_active=bool(request.POST.get("is_active")),
        )

        messages.success(request, "FAQ created successfully.")

        return redirect("dynamic:faq_list")


class FAQUpdateView(View):

    def get(self, request, pk):

        item = get_object_or_404(FAQ, pk=pk)

        return render(
            request, "dynamic/faq/update.html", {"item": item, "active_tab": "faq"}
        )

    def post(self, request, pk):

        item = get_object_or_404(FAQ, pk=pk)

        item.question = request.POST.get("question")
        item.answer = request.POST.get("answer")
        item.is_active = bool(request.POST.get("is_active"))

        item.save()

        messages.success(request, "FAQ updated successfully.")

        return redirect("dynamic:faq_list")


class FAQDeleteView(View):

    def post(self, request, pk):

        item = get_object_or_404(FAQ, pk=pk)

        item.delete()

        messages.success(request, "FAQ deleted successfully.")

        return redirect("dynamic:faq_list")


class AboutListView(LoginRequiredMixin, View):
    login_url = "admin_login"
    template_name = "dynamic/about/about_list.html"

    def get(self, request):

        about_sections = AboutSection.objects.all().order_by("-id")

        context = {"about_sections": about_sections}

        return render(request, self.template_name, context)


class AboutCreateView(LoginRequiredMixin, View):
    login_url = "admin_login"
    template_name = "dynamic/about/about_create.html"

    def get(self, request):

        return render(request, self.template_name)

    def post(self, request):

        AboutSection.objects.create(
            section_tag=request.POST.get("section_tag"),
            main_title=request.POST.get("main_title"),
            main_description=request.POST.get("main_description"),
            button_text=request.POST.get("button_text"),
            button_link=request.POST.get("button_link"),
            about_image=request.FILES.get("about_image"),
            top_badge_text=request.POST.get("top_badge_text"),
            trust_card_title=request.POST.get("trust_card_title"),
            trust_card_subtitle=request.POST.get("trust_card_subtitle"),
            visitors_icon=request.POST.get("visitors_icon"),
            visitors_count=request.POST.get("visitors_count"),
            visitors_label=request.POST.get("visitors_label"),
            students_icon=request.POST.get("students_icon"),
            students_count=request.POST.get("students_count"),
            students_label=request.POST.get("students_label"),
            businesses_icon=request.POST.get("businesses_icon"),
            businesses_count=request.POST.get("businesses_count"),
            businesses_label=request.POST.get("businesses_label"),
            feature_one_icon=request.POST.get("feature_one_icon"),
            feature_one_title=request.POST.get("feature_one_title"),
            feature_two_icon=request.POST.get("feature_two_icon"),
            feature_two_title=request.POST.get("feature_two_title"),
            feature_three_icon=request.POST.get("feature_three_icon"),
            feature_three_title=request.POST.get("feature_three_title"),
            is_active=request.POST.get("is_active") == "on",
        )

        return redirect("dynamic:about_list")


class AboutUpdateView(LoginRequiredMixin, View):
    login_url = "admin_login"

    template_name = "dynamic/about/about_update.html"

    def get(self, request, pk):

        about = get_object_or_404(AboutSection, pk=pk)

        return render(request, self.template_name, {"about": about})

    def post(self, request, pk):

        about = get_object_or_404(AboutSection, pk=pk)

        about.section_tag = request.POST.get("section_tag")

        about.main_title = request.POST.get("main_title")
        about.main_description = request.POST.get("main_description")

        about.button_text = request.POST.get("button_text")
        about.button_link = request.POST.get("button_link")

        if request.FILES.get("about_image"):
            about.about_image = request.FILES.get("about_image")

        about.top_badge_text = request.POST.get("top_badge_text")

        about.trust_card_title = request.POST.get("trust_card_title")
        about.trust_card_subtitle = request.POST.get("trust_card_subtitle")

        about.visitors_icon = request.POST.get("visitors_icon")
        about.visitors_count = request.POST.get("visitors_count")
        about.visitors_label = request.POST.get("visitors_label")

        about.students_icon = request.POST.get("students_icon")
        about.students_count = request.POST.get("students_count")
        about.students_label = request.POST.get("students_label")

        about.businesses_icon = request.POST.get("businesses_icon")
        about.businesses_count = request.POST.get("businesses_count")
        about.businesses_label = request.POST.get("businesses_label")

        about.feature_one_icon = request.POST.get("feature_one_icon")
        about.feature_one_title = request.POST.get("feature_one_title")

        about.feature_two_icon = request.POST.get("feature_two_icon")
        about.feature_two_title = request.POST.get("feature_two_title")

        about.feature_three_icon = request.POST.get("feature_three_icon")
        about.feature_three_title = request.POST.get("feature_three_title")

        about.is_active = request.POST.get("is_active") == "on"

        about.save()

        return redirect("dynamic:about_list")


class AboutDeleteView(LoginRequiredMixin, View):
    login_url = "admin_login"

    def post(self, request, pk):

        about = get_object_or_404(AboutSection, pk=pk)

        about.delete()

        return redirect("dynamic:about_list")


class PromiseSectionListView(LoginRequiredMixin, View):
    login_url = "admin_login"
    template_name = "dynamic/about/promise_section_list.html"

    def get(self, request):
        sections = PromiseSection.objects.all().order_by("-created_at")
        return render(request, self.template_name, {"sections": sections})


class PromiseSectionCreateView(LoginRequiredMixin, View):
    login_url = "admin_login"
    template_name = "dynamic/about/promise_section_create.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        section_name = request.POST.get("section_name")
        title = request.POST.get("title")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"

        section = PromiseSection.objects.create(
            section_name=section_name,
            title=title,
            description=description,
            is_active=is_active,
        )

        return redirect("dynamic:promise_section_edit", pk=section.id)


class PromiseSectionEditView(LoginRequiredMixin, View):
    login_url = "admin_login"
    template_name = "dynamic/about/promise_section_update.html"

    def get(self, request, pk):
        section = get_object_or_404(PromiseSection, pk=pk)
        cards = section.cards.all()
        edit_card_id = request.GET.get("edit_card")
        card_to_edit = None
        if edit_card_id:
            card_to_edit = get_object_or_404(
                PromiseCard, pk=edit_card_id, section=section
            )

        context = {
            "section": section,
            "cards": cards,
            "card_to_edit": card_to_edit,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        section = get_object_or_404(PromiseSection, pk=pk)
        section.section_name = request.POST.get("section_name")
        section.title = request.POST.get("title")
        section.description = request.POST.get("description")
        section.is_active = request.POST.get("is_active") == "on"
        section.save()

        return redirect("dynamic:promise_list")


class PromiseSectionDeleteView(LoginRequiredMixin, View):
    login_url = "admin_login"

    def post(self, request, pk):
        section = get_object_or_404(PromiseSection, pk=pk)
        section.delete()
        return redirect("dynamic:promise_list")


class PromiseCardSaveView(LoginRequiredMixin, View):
    login_url = "admin_login"

    def post(self, request):
        section_id = request.POST.get("section_id")
        card_id = request.POST.get("card_id")
        section = get_object_or_404(PromiseSection, pk=section_id)

        if card_id:
            # Updating an existing card
            card = get_object_or_404(PromiseCard, pk=card_id, section=section)
        else:
            # Creating a new card
            card = PromiseCard(section=section)

        card.icon = request.POST.get("icon")
        card.title = request.POST.get("title")
        card.description = request.POST.get("description")
        card.display_order = int(request.POST.get("display_order", 0) or 0)
        card.is_active = request.POST.get("is_active") == "on"
        card.save()

        return redirect("dynamic:promise_section_edit", pk=section.id)


# ─── DELETE CARD ──────────────────────────────────────────────────────
class PromiseCardDeleteView(LoginRequiredMixin, View):
    login_url = "admin_login"

    def post(self, request, pk):
        card = get_object_or_404(PromiseCard, pk=pk)
        section_id = card.section.id
        card.delete()
        return redirect("dynamic:promise_section_edit", pk=section_id)


# who we are


class WhoWeAreListView(LoginRequiredMixin, ListView):
    login_url = "admin_login"
    model = WhoWeAreSection
    template_name = "dynamic/about/list.html"
    context_object_name = "sections"
    paginate_by = 20

    def get_queryset(self):
        return WhoWeAreSection.objects.all().order_by("-updated_at")


class WhoWeAreFormMixin:
    login_url = "admin_login"
    template_name = "dynamic/about/create.html"
    success_url = reverse_lazy("dynamic:who_we_are_list")

    SIMPLE_FIELDS = [
        "who_we_are_badge",
        "hero_title",
        "hero_description",
        "mission_icon",
        "mission_title",
        "mission_description",
        "popular_services_title",
        "popular_services_sub",
        "our_values_badge",
        "values_title",
        "values_description",
    ]

    # ---- validation ----
    def validate(self, post):
        errors = {}
        if not post.get("hero_title", "").strip():
            errors["hero_title"] = "Hero title is required."
        if not post.get("values_title", "").strip():
            errors["values_title"] = "Values title is required."
        return errors

    # ---- parsing helpers ----
    def build_data_dict(self, post):
        data = {field: post.get(field, "").strip() for field in self.SIMPLE_FIELDS}
        data["is_active"] = post.get("is_active") == "on"
        return data

    def parse_counters(self, post):
        counts = post.getlist("counter_count[]")
        labels = post.getlist("counter_label[]")
        rows = []
        for count, label in zip(counts, labels):
            count, label = count.strip(), label.strip()
            if count or label:
                rows.append({"count": count, "label": label})
        return rows

    def parse_services(self, post):
        names = post.getlist("service_name[]")
        return [n.strip() for n in names if n.strip()]

    def parse_value_items(self, post):
        icons = post.getlist("value_icon[]")
        titles = post.getlist("value_title[]")
        descs = post.getlist("value_description[]")
        rows = []
        for icon, title, desc in zip(icons, titles, descs):
            icon, title, desc = icon.strip(), title.strip(), desc.strip()
            if title or desc:
                rows.append(
                    {
                        "icon": icon or "bi bi-check-circle",
                        "title": title,
                        "description": desc,
                    }
                )
        return rows

    def save_related(self, section, post):
        """Wipe and recreate child rows from the submitted form — simplest
        way to handle add/remove/reorder coming from the dynamic JS rows."""
        section.counters.all().delete()
        for i, row in enumerate(self.parse_counters(post)):
            Counter.objects.create(
                section=section, count=row["count"], label=row["label"], order=i
            )

        section.services.all().delete()
        for i, name in enumerate(self.parse_services(post)):
            PopularService.objects.create(section=section, name=name, order=i)

        section.value_items.all().delete()
        for i, row in enumerate(self.parse_value_items(post)):
            ValueItem.objects.create(
                section=section,
                icon=row["icon"],
                title=row["title"],
                description=row["description"],
                order=i,
            )

    def error_context(self, request, page_title, action, errors):
        post = request.POST
        return {
            "page_title": page_title,
            "action": action,
            "data": self.build_data_dict(post),
            "errors": errors,
            "counters": self.parse_counters(post),
            "services": self.parse_services(post),
            "value_items": self.parse_value_items(post),
        }


# ════════════════════════════════════════════════════════════════
#  CREATE
# ════════════════════════════════════════════════════════════════
class WhoWeAreCreateView(LoginRequiredMixin, WhoWeAreFormMixin, View):
    login_url = "admin_login"
    page_title = "Add Who We Are Section"
    action = "Create"

    def get(self, request):
        context = {
            "page_title": self.page_title,
            "action": self.action,
            "data": {},
            "errors": {},
            "counters": [],
            "services": [],
            "value_items": [],
        }
        return render(request, self.template_name, context)

    def post(self, request):
        post = request.POST
        errors = self.validate(post)

        if errors:
            messages.error(request, "Please fill the Details below.")
            context = self.error_context(request, self.page_title, self.action, errors)
            return render(request, self.template_name, context)

        data = self.build_data_dict(post)
        section = WhoWeAreSection.objects.create(**data)
        self.save_related(section, post)

        messages.success(request, "Section created successfully.")
        return redirect(self.success_url)


# ════════════════════════════════════════════════════════════════
#  UPDATE
# ════════════════════════════════════════════════════════════════
class WhoWeAreUpdateView(LoginRequiredMixin, WhoWeAreFormMixin, View):
    page_title = "Edit Who We Are Section"
    action = "Update"

    def get(self, request, pk):
        section = get_object_or_404(WhoWeAreSection, pk=pk)
        data = {field: getattr(section, field) for field in self.SIMPLE_FIELDS}
        data["is_active"] = section.is_active

        context = {
            "page_title": self.page_title,
            "action": self.action,
            "data": data,
            "errors": {},
            "counters": list(section.counters.all()),
            "services": [s.name for s in section.services.all()],
            "value_items": list(section.value_items.all()),
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        section = get_object_or_404(WhoWeAreSection, pk=pk)
        post = request.POST
        errors = self.validate(post)

        if errors:
            messages.error(request, "Please fill the details below.")
            context = self.error_context(request, self.page_title, self.action, errors)
            return render(request, self.template_name, context)

        data = self.build_data_dict(post)
        for field, value in data.items():
            setattr(section, field, value)
        section.save()
        self.save_related(section, post)

        messages.success(request, "Section updated successfully.")
        return redirect(self.success_url)


# ════════════════════════════════════════════════════════════════
#  DELETE
# ════════════════════════════════════════════════════════════════
class WhoWeAreDeleteView(LoginRequiredMixin, View):
    template_name = "dynamic/about/delete.html"
    success_url = reverse_lazy("dynamic:who_we_are_list")

    def get(self, request, pk):
        """Confirmation page before deleting."""
        section = get_object_or_404(WhoWeAreSection, pk=pk)
        return render(request, self.template_name, {"section": section})

    def post(self, request, pk):
        section = get_object_or_404(WhoWeAreSection, pk=pk)
        section.delete()
        messages.success(request, "Section deleted.")
        return redirect(self.success_url)


# your partner
class PartnerSectionListView(LoginRequiredMixin, View):

    template_name = "dynamic/about/partner_list.html"

    def get(self, request):

        sections = BulkPartnerSection.objects.all().order_by("-id")

        return render(request, self.template_name, {"sections": sections})


class PartnerSectionCreateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/partner_create.html"

    def get(self, request):

        return render(request, self.template_name)

    def post(self, request):

        section = BulkPartnerSection.objects.create(
            section_name=request.POST.get("section_name"),
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            is_active=request.POST.get("is_active") == "on",
        )

        images = request.FILES.getlist("partner_images")
        for img in images:
            PartnerImage.objects.create(section=section, image=img)

        return redirect("dynamic:partner_list")


class PartnerSectionUpdateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/partner_update.html"

    def get(self, request, pk):

        section = get_object_or_404(BulkPartnerSection, pk=pk)

        return render(request, self.template_name, {"section": section})

    def post(self, request, pk):

        section = get_object_or_404(BulkPartnerSection, pk=pk)

        section.section_name = request.POST.get("section_name")

        section.title = request.POST.get("title")

        section.description = request.POST.get("description")

        section.is_active = request.POST.get("is_active") == "on"

        section.save()

        # Handle bulk deletion of selected images
        delete_image_ids = request.POST.getlist("delete_images")
        if delete_image_ids:
            PartnerImage.objects.filter(
                id__in=delete_image_ids, section=section
            ).delete()

        images = request.FILES.getlist("partner_images")
        for img in images:
            PartnerImage.objects.create(section=section, image=img)

        if request.POST.get("action") == "bulk_delete":
            return redirect("dynamic:partner_section_edit", pk=pk)

        return redirect("dynamic:partner_list")


class PartnerSectionDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk):

        section = get_object_or_404(BulkPartnerSection, pk=pk)

        section.delete()

        return redirect("dynamic:partner_list")


class PartnerImageListView(LoginRequiredMixin, View):

    template_name = "dynamic/about/image_list.html"

    def get(self, request, section_id):

        section = get_object_or_404(BulkPartnerSection, pk=section_id)

        images = section.images.all()

        return render(
            request, self.template_name, {"section": section, "images": images}
        )


class PartnerImageCreateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/image_create.html"

    def get(self, request, section_id):

        section = get_object_or_404(BulkPartnerSection, pk=section_id)

        return render(request, self.template_name, {"section": section})

    def post(self, request, section_id):

        section = get_object_or_404(BulkPartnerSection, pk=section_id)

        image = request.FILES.get("image")

        if image:

            PartnerImage.objects.create(section=section, image=image)

        return redirect("dynamic:partner_image_list", section_id=section.id)


class PartnerImageUpdateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/image_update.html"

    def get(self, request, pk):

        image = get_object_or_404(PartnerImage, pk=pk)

        return render(request, self.template_name, {"image_obj": image})

    def post(self, request, pk):

        image_obj = get_object_or_404(PartnerImage, pk=pk)

        image = request.FILES.get("image")

        if image:
            image_obj.image = image
            image_obj.save()

        return redirect("dynamic:partner_image_list", section_id=image_obj.section.id)


class PartnerImageDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk):

        image = get_object_or_404(PartnerImage, pk=pk)

        section_id = image.section.id

        image.delete()

        return redirect("dynamic:partner_section_edit", pk=section_id)


class TeamCreateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/team_create.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        TeamSection.objects.create(
            section_name=request.POST.get("section_name"),
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            image=request.FILES.get("image"),
            name=request.POST.get("name"),
            role=request.POST.get("role"),
            member_description=request.POST.get("member_description"),
            is_active=request.POST.get("is_active") == "on",
        )

        return redirect("dynamic:team_list")


class TeamUpdateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/team_update.html"

    def get(self, request, pk):

        team = get_object_or_404(TeamSection, pk=pk)

        return render(request, self.template_name, {"team": team})

    def post(self, request, pk):

        team = get_object_or_404(TeamSection, pk=pk)

        team.section_name = request.POST.get("section_name")

        team.title = request.POST.get("title")

        team.description = request.POST.get("description")

        team.name = request.POST.get("name")

        team.role = request.POST.get("role")

        team.member_description = request.POST.get("member_description")

        if request.FILES.get("image"):
            team.image = request.FILES.get("image")

        team.is_active = request.POST.get("is_active") == "on"

        team.save()

        return redirect("dynamic:team_list")


class TeamListView(LoginRequiredMixin, View):

    template_name = "dynamic/about/team_list.html"

    def get(self, request):

        teams = TeamSection.objects.all()

        return render(request, self.template_name, {"teams": teams})


class TeamDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk):

        team = get_object_or_404(TeamSection, pk=pk)

        team.delete()

        return redirect("dynamic:team_list")


# contact


class ContactListView(LoginRequiredMixin, View):

    template_name = "dynamic/about/contact_list.html"

    def get(self, request):

        contacts = ContactPage.objects.all().order_by("-id")

        return render(request, self.template_name, {"contacts": contacts})


class ContactCreateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/contact_create.html"

    def get(self, request):

        return render(request, self.template_name)

    def post(self, request):

        contact = ContactPage.objects.create(
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            form_title=request.POST.get("form_title"),
            button_text=request.POST.get("button_text"),
            map_iframe=request.POST.get("map_iframe"),
            is_active=request.POST.get("is_active") == "on",
        )

        # Contact Features

        feature_titles = request.POST.getlist("feature_title[]")

        feature_icons = request.POST.getlist("feature_icon[]")

        feature_values = request.POST.getlist("feature_value[]")

        for i in range(len(feature_titles)):

            if feature_titles[i]:

                ContactFeature.objects.create(
                    page=contact,
                    icon=feature_icons[i],
                    title=feature_titles[i],
                    value=feature_values[i],
                )

        # Form Fields

        field_labels = request.POST.getlist("field_label[]")

        field_placeholders = request.POST.getlist("field_placeholder[]")

        field_types = request.POST.getlist("field_type[]")

        for i in range(len(field_labels)):

            if field_labels[i]:

                ContactFormField.objects.create(
                    page=contact,
                    label=field_labels[i],
                    placeholder=field_placeholders[i],
                    field_type=field_types[i],
                )

        return redirect("dynamic:contact_list")


class ContactUpdateView(LoginRequiredMixin, View):

    template_name = "dynamic/about/contact_update.html"

    def get(self, request, pk):

        contact = get_object_or_404(ContactPage, pk=pk)

        return render(
            request,
            self.template_name,
            {
                "contact": contact,
                "features": contact.features.all(),
                "fields": contact.form_fields.all(),
            },
        )

    def post(self, request, pk):

        contact = get_object_or_404(ContactPage, pk=pk)

        contact.title = request.POST.get("title")

        contact.description = request.POST.get("description")

        contact.form_title = request.POST.get("form_title")

        contact.button_text = request.POST.get("button_text")

        contact.map_iframe = request.POST.get("map_iframe")

        contact.is_active = request.POST.get("is_active") == "on"

        contact.save()

        # Remove old features
        contact.features.all().delete()

        feature_titles = request.POST.getlist("feature_title[]")

        feature_icons = request.POST.getlist("feature_icon[]")

        feature_values = request.POST.getlist("feature_value[]")

        for i in range(len(feature_titles)):

            if feature_titles[i]:

                ContactFeature.objects.create(
                    page=contact,
                    icon=feature_icons[i],
                    title=feature_titles[i],
                    value=feature_values[i],
                )

        # Remove old form fields
        contact.form_fields.all().delete()

        field_labels = request.POST.getlist("field_label[]")

        field_placeholders = request.POST.getlist("field_placeholder[]")

        field_types = request.POST.getlist("field_type[]")

        for i in range(len(field_labels)):

            if field_labels[i]:

                ContactFormField.objects.create(
                    page=contact,
                    label=field_labels[i],
                    placeholder=field_placeholders[i],
                    field_type=field_types[i],
                )

        return redirect("dynamic:contact_list")


class ContactDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk):

        contact = get_object_or_404(ContactPage, pk=pk)

        contact.delete()

        return redirect("dynamic:contact_list")


class PlaceListView(View):

    template_name = "dynamic/visitingplaces/list.html"

    def get(self, request):

        items_queryset = TouristPlace.objects.all().order_by("-id")

        items = paginate_queryset(request, items_queryset, per_page=10)

        return render(
            request,
            self.template_name,
            {
                "items": items,
                "page_obj": items,
                "active_tab": "place_list",
            },
        )


class PlaceCreateView(View):
    template_name = "dynamic/visitingplaces/create.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        TouristPlace.objects.create(
            title=request.POST.get("title"),
            location=request.POST.get("location"),
            description=request.POST.get("description"),
            rating=request.POST.get("rating"),
            image=request.FILES.get("image"),
            is_active=True if request.POST.get("is_active") else False,
        )

        return redirect("dynamic:place_list")


class PlaceUpdateView(View):
    template_name = "dynamic/visitingplaces/update.html"

    def get(self, request, pk):

        item = get_object_or_404(TouristPlace, pk=pk)

        return render(request, self.template_name, {"item": item})

    def post(self, request, pk):

        item = get_object_or_404(TouristPlace, pk=pk)

        item.title = request.POST.get("title")
        item.location = request.POST.get("location")
        item.description = request.POST.get("description")
        item.rating = request.POST.get("rating")

        item.is_active = True if request.POST.get("is_active") else False

        if request.FILES.get("image"):
            item.image = request.FILES.get("image")

        item.save()

        return redirect("dynamic:place_list")


class PlaceDeleteView(View):

    def post(self, request, pk):

        place = get_object_or_404(TouristPlace, pk=pk)

        place.delete()

        return redirect("dynamic:place_list")







# privacy policy and terms & conditions


class TermsListView(ListView):
    model = TermsAndConditions
    template_name = 'dynamic/terms/terms_list.html'
    context_object_name = 'items'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Terms & Conditions"
        context['create_url'] = 'terms_create'
        context['update_url'] = 'terms_update'
        context['delete_url'] = 'terms_delete'
        return context

class TermsCreateView(CreateView):
    model = TermsAndConditions
    fields = ['title', 'content', 'is_active']
    template_name = 'dynamic/terms/terms_create.html'
    success_url = reverse_lazy('dynamic:terms_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create Terms & Conditions"
        return context

class TermsUpdateView(UpdateView):
    model = TermsAndConditions
    fields = ['title', 'content', 'is_active']
    template_name = 'dynamic/terms/terms_create.html'
    success_url = reverse_lazy('dynamic:terms_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Edit Terms & Conditions"
        return context

class TermsDeleteView(View):

    def post(self, request, pk):
        terms = get_object_or_404(TermsAndConditions, pk=pk)
        terms.delete()

        messages.success(request, "Terms & Conditions deleted successfully.")

        return redirect("dynamic:terms_list")




# --- PRIVACY POLICY VIEWS ---

class PrivacyListView(ListView):
    model = PrivacyPolicy
    template_name = 'dynamic/privacy/privacy_list.html'
    context_object_name = 'items'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Privacy Policies"
        context['create_url'] = 'privacy_create'
        context['update_url'] = 'privacy_update'
        context['delete_url'] = 'privacy_delete'
        return context

class PrivacyCreateView(CreateView):
    model = PrivacyPolicy
    fields = ['title', 'content', 'is_active']
    template_name = 'dynamic/privacy/privacy_create.html'
    success_url = reverse_lazy('dynamic:privacy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create Privacy Policy"
        return context

class PrivacyUpdateView(UpdateView):
    model = PrivacyPolicy
    fields = ['title', 'content', 'is_active']
    template_name = 'dynamic/privacy/privacy_create.html'
    success_url = reverse_lazy('dynamic:privacy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Edit Privacy Policy"
        return context



class PrivacyDeleteView(View):

    def post(self, request, pk):
        privacy = get_object_or_404(PrivacyPolicy, pk=pk)
        privacy.delete()

        messages.success(request, "Privacy Policy deleted successfully.")

        return redirect("dynamic:privacy_list")
    

# contact page details

class SuperAdminContactEnquiryView(LoginRequiredMixin, View):
    """Super Admin - View all Contact Enquiries with filters and delete"""

    template_name = "accounts/admin/admin_contacts.html"

    def get(self, request):
        enquiries = ContactEnquiry.objects.all().order_by("-created_at")

        # --- Date range filter ---
        start_date = request.GET.get("start_date")
        end_date   = request.GET.get("end_date")
        if start_date:
            enquiries = enquiries.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            enquiries = enquiries.filter(created_at__date__lte=parse_date(end_date))

        # --- Subject filter ---
        selected_subject = request.GET.get("subject", "")
        if selected_subject:
            enquiries = enquiries.filter(subject=selected_subject)

        # All distinct subjects for the dropdown
        all_subjects = (
            ContactEnquiry.objects
            .values_list("subject", flat=True)
            .distinct()
            .order_by("subject")
        )

        context = {
            "enquiries"       : enquiries,
            "all_subjects"    : all_subjects,
            "selected_subject": selected_subject,
            "start_date"      : start_date or "",
            "end_date"        : end_date   or "",
            "active_tab"      : "contact_enquiries",
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Delete a single enquiry"""
        enquiry_id = request.POST.get("enquiry_id")
        enquiry = get_object_or_404(ContactEnquiry, id=enquiry_id)
        enquiry.delete()
        # Preserve active filters after delete
        params = request.POST.get("query_string", "")
        return redirect(f"{request.path}?{params}" if params else request.path)


class PopularBusinessSearchListView(LoginRequiredMixin, View):
    template_name = "dynamic/popular_business_searches/list.html"

    def get(self, request):
        from django.db.models import Q
        queryset = PopularBusinessSearch.objects.select_related("business", "business__category").order_by("-search_count")
        
        # Simple search filter
        search = request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(business__company_name__icontains=search) | Q(business__category__name__icontains=search)
            )

        status_filter = request.GET.get("status", "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        items = paginate_queryset(request, queryset, per_page=10)
        
        return render(
            request,
            self.template_name,
            {
                "items": items,
                "page_obj": items,
                "search": search,
                "status_filter": status_filter,
                "active_tab": "popular_business_searches",
            }
        )


class ApproveBusinessSearchView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(PopularBusinessSearch, pk=pk)
        item.status = "approved"
        item.save()
        messages.success(request, f"Search for '{item.business.company_name}' approved successfully.")
        return redirect("dynamic:popular_business_searches_list")


class RejectBusinessSearchView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(PopularBusinessSearch, pk=pk)
        item.status = "fake"
        item.save()
        messages.success(request, f"Search for '{item.business.company_name}' marked as fake.")
        return redirect("dynamic:popular_business_searches_list")