from django.db import models
from ckeditor.fields import RichTextField


class AboutSection(models.Model):
    # Section Header
    section_tag = models.CharField(max_length=100, default="ABOUT JUSTKLICK")

    main_title = models.CharField(max_length=255, help_text="Main heading")

    main_description = models.TextField(help_text="About section description")

    # Button
    button_text = models.CharField(max_length=100, default="Explore Features")

    button_link = models.CharField(max_length=255, blank=True)

    # Main Image
    about_image = models.ImageField(upload_to="about/")

    # Top Floating Badge
    top_badge_text = models.CharField(
        max_length=100, default="Verified Education Services"
    )

    # Trust Card
    trust_card_title = models.CharField(max_length=100, default="Trusted")

    trust_card_subtitle = models.CharField(max_length=100, default="Student Services")

    # Statistics - Visitors
    visitors_icon = models.CharField(max_length=100)
    visitors_count = models.CharField(max_length=50)
    visitors_label = models.CharField(max_length=50, default="Visitors")

    # Statistics - Students
    students_icon = models.CharField(max_length=100)
    students_count = models.CharField(max_length=50)
    students_label = models.CharField(max_length=50, default="Students")

    # Statistics - Businesses
    businesses_icon = models.CharField(max_length=100)
    businesses_count = models.CharField(max_length=50)
    businesses_label = models.CharField(max_length=50, default="Businesses")

    # Bottom Features
    feature_one_icon = models.CharField(max_length=100)
    feature_one_title = models.CharField(max_length=100, default="Verified Providers")

    feature_two_icon = models.CharField(max_length=100)
    feature_two_title = models.CharField(max_length=100, default="Student Enquiries")

    feature_three_icon = models.CharField(max_length=100)
    feature_three_title = models.CharField(max_length=100, default="Smart Discovery")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "About Section"
        verbose_name_plural = "About Section"

    def __str__(self):
        return self.main_title


class WhyChooseUss(models.Model):

    title = models.CharField(max_length=200)

    description = models.TextField()

    icon = models.ImageField(upload_to="why_choose_us/")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class FAQ(models.Model):

    question = models.CharField(max_length=500)

    answer = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ["id"]


class ServiceSection(models.Model):
    section_title = models.CharField(max_length=100)

    title = models.CharField(max_length=255)

    description = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class PromiseSection(models.Model):
    section_name = models.CharField(max_length=100, help_text="Example: OUR PROMISE")

    title = models.CharField(max_length=255, help_text="Main Heading")

    description = models.TextField(help_text="Section Description")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PromiseCard(models.Model):
    section = models.ForeignKey(
        PromiseSection, on_delete=models.CASCADE, related_name="cards"
    )

    icon = models.CharField(
        max_length=100, help_text="Bootstrap Icon Example: bi bi-lightning-charge"
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class BulkPartnerSection(models.Model):
    section_name = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def get_images(self):
        return [img.image.url for img in self.images.all() if img.image]

    def __str__(self):
        return self.title


class PartnerImage(models.Model):
    section = models.ForeignKey(
        BulkPartnerSection, on_delete=models.CASCADE, related_name="images"
    )

    image = models.ImageField(upload_to="partners/")

    def __str__(self):
        return f"Image for {self.section.title}"


# who we are section
class WhoWeAreSection(models.Model):
    """
    Content for the public 'About / Who We Are' page.
    Only one section is meant to be `is_active=True` at a time — that's
    the one your public About page (justklick-web.vercel.app/about)
    should query and render. Keeping old/draft rows around as
    is_active=False lets you preview or roll back content.
    """

    # ── WHO WE ARE (left column) ───────────────────────────────
    who_we_are_badge = models.CharField(
        max_length=60,
        default="WHO WE ARE",
        help_text="Small pill label above the hero title.",
    )
    hero_title = models.CharField(
        max_length=200,
        help_text="Main heading, e.g. 'Built to simplify trusted local discovery.'",
    )
    hero_description = models.TextField(blank=True)

    mission_icon = models.CharField(
        max_length=60,
        default="bi bi-flag",
        help_text="Bootstrap icon class, e.g. bi bi-flag",
    )
    mission_title = models.CharField(max_length=120, default="Our mission")
    mission_description = models.TextField(blank=True, default="mission description")

    popular_services_title = models.CharField(
        max_length=150, default="Popular services on JustKlick"
    )
    popular_services_sub = models.CharField(max_length=255, blank=True)

    # ── OUR VALUES (right column) ──────────────────────────────
    our_values_badge = models.CharField(max_length=60, default="OUR VALUES")
    values_title = models.CharField(
        max_length=200, help_text="e.g. 'What we stand for'"
    )
    values_description = models.TextField(blank=True)

    # ── meta ────────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=False,
        help_text="Only one section should be active (published) at a time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Who We Are Section"
        verbose_name_plural = "Who We Are Sections"

    def __str__(self):
        return self.hero_title or f"Who We Are Section #{self.pk}"

    def save(self, *args, **kwargs):
        # Enforce "only one active section" automatically.
        if self.is_active:
            WhoWeAreSection.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Counter(models.Model):
    """e.g. 100+ / VERIFIED PARTNERS, 24/7 / STUDENT SUPPORT, 6+ / SERVICE CATEGORIES"""

    section = models.ForeignKey(
        WhoWeAreSection, related_name="counters", on_delete=models.CASCADE
    )
    count = models.CharField(max_length=20, help_text="e.g. 100+, 24/7, 6+")
    label = models.CharField(max_length=60, help_text="e.g. VERIFIED PARTNERS")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.count} — {self.label}"


class PopularService(models.Model):
    """e.g. Overseas, Software Institutes, Coaching Centers, Hostels, Colleges, Competitive Exams"""

    section = models.ForeignKey(
        WhoWeAreSection, related_name="services", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class ValueItem(models.Model):
    """e.g. Student-first Discovery, Verified Service Providers, Cross-platform Reach, Our platform promise"""

    section = models.ForeignKey(
        WhoWeAreSection, related_name="value_items", on_delete=models.CASCADE
    )
    icon = models.CharField(max_length=60, default="bi bi-check-circle")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


# team section
class TeamSection(models.Model):

    section_name = models.CharField(max_length=100, default="OUR TEAM")

    title = models.CharField(max_length=255, default="Leadership behind JustKlick")

    description = models.TextField()

    image = models.ImageField(upload_to="team/")

    name = models.CharField(max_length=255)

    role = models.CharField(max_length=255)

    member_description = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# contact


class ContactPage(models.Model):

    title = models.CharField(max_length=255)

    description = models.TextField()

    form_title = models.CharField(max_length=255, default="Send Us a Message")

    button_text = models.CharField(max_length=100, default="Submit Message")

    map_iframe = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ContactFeature(models.Model):

    page = models.ForeignKey(
        ContactPage, on_delete=models.CASCADE, related_name="features"
    )

    icon = models.CharField(max_length=100)

    title = models.CharField(max_length=255)

    value = models.TextField()

    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class ContactFormField(models.Model):

    page = models.ForeignKey(
        ContactPage, on_delete=models.CASCADE, related_name="form_fields"
    )

    label = models.CharField(max_length=255)

    placeholder = models.CharField(max_length=255)

    FIELD_TYPES = (
        ("text", "Text"),
        ("email", "Email"),
        ("number", "Number"),
        ("textarea", "Textarea"),
    )

    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)

    required = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.label


class ContactEnquiry(models.Model):

    full_name = models.CharField(max_length=255)

    email = models.EmailField()

    phone = models.CharField(max_length=20)

    subject = models.CharField(max_length=255)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class TouristPlace(models.Model):
    image = models.ImageField(upload_to="tourist_places/")
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    description = models.TextField()
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PopularSearch(models.Model):
    """Track popular category searches"""

    from apps.categories.models import Category

    category = models.OneToOneField(
        "categories.Category", on_delete=models.CASCADE, related_name="popular_search"
    )
    search_count = models.PositiveIntegerField(default=0)
    display_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-search_count", "-is_featured", "display_order"]
        verbose_name = "Popular Search"
        verbose_name_plural = "Popular Searches"

    def __str__(self):
        return f"{self.category.name} - {self.search_count} searches"

    @classmethod
    def increment_search(cls, category_id):
        """Increment search count for a category"""
        obj, created = cls.objects.get_or_create(category_id=category_id)
        obj.search_count += 1
        obj.save(update_fields=["search_count"])
        return obj


class PopularBusinessSearch(models.Model):
    """Track popular business searches"""

    business = models.OneToOneField(
        "businesses.Business", on_delete=models.CASCADE, related_name="popular_business_search"
    )
    search_count = models.PositiveIntegerField(default=0)
    display_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("fake", "Fake Search")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-search_count", "-is_featured", "display_order"]
        verbose_name = "Popular Business Search"
        verbose_name_plural = "Popular Business Searches"

    def __str__(self):
        return f"{self.business.company_name} - {self.search_count} searches"

    @classmethod
    def increment_search_bulk(cls, business_ids):
        """Bulk increment search count and create missing search tracking records"""
        if not business_ids:
            return
        
        # Query existing records
        existing = cls.objects.filter(business_id__in=business_ids)
        existing_map = {obj.business_id: obj for obj in existing}
        
        # Update existing records
        for obj in existing:
            obj.search_count += 1
            obj.save(update_fields=["search_count"])
            
        # Create missing records
        missing_ids = set(business_ids) - set(existing_map.keys())
        if missing_ids:
            cls.objects.bulk_create([
                cls(business_id=bid, search_count=1, status="pending")
                for bid in missing_ids
            ])



# privacy policy and terms & conditions

class TermsAndConditions(models.Model):
    title = models.CharField(
        max_length=200,
        default="Terms & Conditions"
    )

    content = RichTextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Terms & Conditions"
        verbose_name_plural = "Terms & Conditions"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class PrivacyPolicy(models.Model):
    title = models.CharField(
        max_length=200,
        default="Privacy Policy"
    )

    content = RichTextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Privacy Policy"
        verbose_name_plural = "Privacy Policy"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title