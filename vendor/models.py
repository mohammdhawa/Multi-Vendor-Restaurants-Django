from django.db import models
from django.utils.text import slugify

from accounts.models import User, Profile
from accounts.utils import send_vendor_account_status_email


class Vendor(models.Model):
    user = models.OneToOneField(User, related_name='user', on_delete=models.CASCADE)
    user_profile = models.OneToOneField(Profile, related_name='vendor_profile', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=100)
    vendor_license = models.ImageField(upload_to='vendor/license_pictures')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.vendor_name

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Step 1: Save without slug if it's a new instance so we get an ID
        if is_new:
            super().save(*args, **kwargs)

        # Step 2: Set slug with ID and vendor_name, if slug is missing
        if not self.slug:
            base_slug = f"{self.id}-{slugify(self.vendor_name)}"
            self.slug = base_slug
            # Save again to store the slug
            super().save(update_fields=["slug"])

        # If updating and checking approval status
        if not is_new:
            original = Vendor.objects.get(pk=self.pk)
            if original.is_approved != self.is_approved:
                send_vendor_account_status_email(self.user, self.is_approved)

        if not is_new:
            super().save(*args, **kwargs)