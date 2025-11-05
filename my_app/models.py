from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import hashlib
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class user(models.Model):
    full_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=False, null=False)
    phone_no = models.CharField(max_length=20)
    password = models.CharField(max_length=255, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(
        max_length=1,
        choices=[('0', 'super_admin'), ('1', 'admin'), ('2', 'user')], 
        default='1', null=False,
        blank=False
    )
    status = models.CharField(
        max_length=1,
        choices=[('0', 'inactive'), ('1', 'active'), ('5', 'deleted')], 
        default='1', null=False,
        blank=False
    )

    class Meta:
        db_table = 'user'
    

    def clean(self):

        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError("Enter a valid email address!")

        if len(self.password) < 6:
            raise ValidationError({
                'password': 'Password must be at least 6 characters long.'
            })

        if user.objects.filter(
            email=self.email,
            status__in=['0', '1']).exclude(id= self.id).exists():
            raise ValidationError({'email':'An employee with this email already exists.'})


    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
            print(f"After hashing :{self.password}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"
AUTH_USER_MODEL = 'my_app.CostomUser'

from django.db import models

class company(models.Model): 
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=False, null=False, unique=True)
    phone_no = models.CharField(max_length=20, blank=False)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=1,
        choices=[('0', 'inactive'), ('1', 'active'), ('5', 'deleted')], 
        default='1', null=False,
        blank=False
    ) 
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'company'

    def get_follower_count(self):
        return self.followers.count()
    
    def clean(self):

        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError("Enter a valid email address!")
        

        if company.objects.filter(
            email=self.email,
            status__in=['0', '1']
        ).exclude(id=self.id).exists():
            raise ValidationError({'email': 'A company with this email already exists.'})

        if company.objects.filter(
            name=self.name,
            status__in=['0', '1']
        ).exclude(id=self.id).exists():
            raise ValidationError({'name': 'A company with this name already exists.'})

        if self.phone_no:
            import re
            phone_digits = re.sub(r'\D', '', self.phone_no)
            if len(phone_digits) < 10:
                raise ValidationError({'phone_no': 'Phone number must contain at least 10 digits.'})

        if company.objects.filter(
            email=self.email,
            status__in=['0', '1']).exclude(id= self.id).exists():
            raise ValidationError({'email':'An company with this email already exists.'})
        

class company_followers(models.Model):
    company = models.ForeignKey(
        'company',
        on_delete=models.CASCADE,
        related_name='followers'
    )
    user = models.ForeignKey(
        'user',
        on_delete=models.CASCADE,
        related_name='following_companies'
    )
    updated_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=1,
        choices=[('0', 'unfollwed'), ('1', 'following'), ('5', 'deleted')], 
        default='1', null=False,
        blank=False
    ) 
    class Meta:
        db_table = 'company_followers'
        unique_together = ['company', 'user']

    def __str__(self):
        return f"{self.user.full_name} follows {self.company.name}"

class job_posts(models.Model):
    STATUS_CHOICES = [
        ('1', 'Active'),
        ('0', 'Inactive'),
        ('5', 'Deleted'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ]
    company = models.ForeignKey(
        'company',
        on_delete=models.CASCADE,
        related_name='job_posts'
    )

    job_title = models.CharField(max_length=255, blank=False, null=False)
    job_description = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time', blank=False, null=False)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'job_posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_title} - {self.company.name}"
