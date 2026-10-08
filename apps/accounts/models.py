from django.conf import settings
from django.contrib.auth.models import AbstractUser,Permission
from django.db import models




class BaseModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s_records"
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s_records"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True,null=True)
    permissions = models.ManyToManyField(Permission,blank=True,related_name="roles")

    def __str__(self):
        return self.name


class User(AbstractUser):
    username = models.CharField(max_length=150,unique=False,blank=True,null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15,unique=True,null=True,blank=True)
    role = models.ForeignKey(Role,on_delete=models.SET_NULL,null=True,blank=True,related_name="users")
    google_sub = models.CharField(max_length=255,blank=True,null=True)
    profile_image = models.URLField(blank=True,null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to="profile_images/",blank=True,null=True)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["username","first_name","last_name"]
    
    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if self.is_superuser and not self.role:

            role, _ = Role.objects.get_or_create(
                name="SuperAdmin"
            )

            self.role = role

            super().save(
                update_fields=["role"]
            )

    def __str__(self):
        return self.email

  
class OTP(BaseModel):

    PURPOSE_CHOICES = (
        ("REGISTER", "Register"),
        ("LOGIN", "Login"),
    )
    email = models.EmailField(null=True,blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    last_resend_at = models.DateTimeField(null=True,blank=True)
    phone = models.CharField( max_length=15)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20,choices=PURPOSE_CHOICES)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    resend_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True,blank=True)
    ip_address = models.GenericIPAddressField(null=True,blank=True)
    blocked_until = models.DateTimeField(null=True,blank=True)
    user_agent = models.TextField(blank=True,null=True)
    
    
    def __str__(self):
        return f"{self.phone} - {self.purpose}"


class LoginHistory(BaseModel):

    LOGIN_TYPES = (
        ("OTP", "OTP"),
        ("GOOGLE", "GOOGLE"),
    )

    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="login_histories")
    login_type = models.CharField(max_length=20,choices=LOGIN_TYPES)
    ip_address = models.GenericIPAddressField(null=True,blank=True)
    user_agent = models.TextField(blank=True,null=True)
    is_success = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.login_type}"
    
    
    
class StudentOnboarding(BaseModel):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_onboarding"
    )
    father_name = models.CharField(max_length=255)
    college_code = models.CharField(max_length=100)
    dept_course = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=50)
    year_of_study = models.CharField(max_length=50)
    cgpa_percentage = models.CharField(max_length=50)
    course_reason = models.JSONField(default=list)
    area_of_interest = models.JSONField(default=list)
    skills_to_develop = models.JSONField(default=list)
    plan_after_graduation = models.CharField(max_length=100)
    interested_abroad = models.CharField(max_length=20)
    preferred_country = models.CharField(max_length=100,blank=True,null=True)
    career_goal = models.CharField(max_length=100)
    internship_completed = models.BooleanField(default=False)
    interested_in_internship = models.BooleanField(default=False)
    certifications = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.email




class BlacklistedToken(BaseModel):
    jti = models.CharField(max_length=255,unique=True)

    def __str__(self):
        return self.jti


class Lead(BaseModel):

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='leads'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.name} - {self.business.company_name}"
    
    

