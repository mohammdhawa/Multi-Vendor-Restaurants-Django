from django.db import models
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

    def __str__(self):
        return self.vendor_name

    def save(self, *args, **kwargs):
        if self.pk is not None:
            # update
            original_status = Vendor.objects.get(pk=self.pk)
            if original_status.is_approved != self.is_approved:
                if self.is_approved:
                    send_vendor_account_status_email(self.user, True)
                else:
                    # send email
                    send_vendor_account_status_email(self.user, False)
        return super(Vendor, self).save(*args, **kwargs)