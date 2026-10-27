import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        ADMIN = 'ADMIN', 'Administrator'
        DELIVERY_PERSON = 'DELIVERY_PERSON', 'Delivery Person'

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    reset_token = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        if not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser or self.is_staff

    @property
    def is_delivery_person(self):
        return self.role == self.Role.DELIVERY_PERSON

    def __str__(self):
        return f"{self.email} ({self.role})"


class Address(models.Model):
    class AddressType(models.TextChoices):
        HOSPITAL = 'HOSPITAL', 'Hospital / Medical Center'
        CLINIC = 'CLINIC', 'Clinic / Practice'
        LABORATORY = 'LABORATORY', 'Diagnostic Laboratory'
        OFFICE = 'OFFICE', 'Corporate / Institutional Office'
        HOME = 'HOME', 'Home / Residence'
        OTHER = 'OTHER', 'Other Destination'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    landmark = models.CharField(max_length=150, blank=True, null=True)
    pin_code = models.CharField(max_length=15)
    address_type = models.CharField(max_length=30, choices=AddressType.choices, default=AddressType.HOSPITAL)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        else:
            if not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
                self.is_default = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        was_default = self.is_default
        user = self.user
        super().delete(*args, **kwargs)
        if was_default:
            next_addr = Address.objects.filter(user=user).order_by('-created_at').first()
            if next_addr:
                next_addr.is_default = True
                next_addr.save(update_fields=['is_default'])

    def __str__(self):
        return f"{self.full_name} ({self.address_type}) - {self.address_line[:30]} ({self.pin_code})"
