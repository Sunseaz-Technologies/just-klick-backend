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
