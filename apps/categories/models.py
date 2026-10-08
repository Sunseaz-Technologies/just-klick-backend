from django.db import models
from django.utils.text import slugify
class Category(models.Model):

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    banner_image = models.ImageField(
        upload_to="categories/banners/",
        null=True,
        blank=True,
        help_text="Used as the background/banner photo on homepage featured category cards",
    )
    subtitle = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Short tagline shown on the featured card, e.g. 'Trusted consultants'",
    )
    url = models.URLField(
        null=True,
        blank=True,
        help_text="External link associated with this category",
    )
    color = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Hex color code for the card background/accent, e.g. #0F9D58",
    )
    is_card = models.BooleanField(
        default=False,
        help_text="Show this category as a featured card on the homepage",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Controls display order of featured cards on the homepage (lower number = shown first)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug
        super().save(*args, **kwargs)


class CategoryField(models.Model):

    FIELD_TYPE_CHOICES = [
        ("text", "Text"),
        ("number", "Number"),
        ("textarea", "Textarea"),
        ("checkbox", "Checkbox"),
        ("radio", "Radio"),
        ("select", "Select"),
        ("range", "Range"),
    ]

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    label = models.CharField(max_length=255)
    field_key = models.SlugField(max_length=100, blank=True)
    field_type = models.CharField(
        max_length=20, choices=FIELD_TYPE_CHOICES, default="text"
    )
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='Options for checkbox, radio, select fields. e.g. ["Boys PG", "Girls PG"]',
    )
    show_as_filter = models.BooleanField(
        default=False, help_text="Show this field as a filter on listing page"
    )
    placeholder = models.CharField(max_length=255, null=True, blank=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Category Field"
        verbose_name_plural = "Category Fields"

    def __str__(self):
        return f"{self.category.name} - {self.label}"

    def save(self, *args, **kwargs):
        if not self.field_key:
            self.field_key = slugify(self.label)
        super().save(*args, **kwargs)