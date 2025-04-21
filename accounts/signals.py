from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        print('User profile created')
    else:
        try:
            profile = Profile.objects.get(user=instance)
            profile.save()
        except:
            # Create the user profile if not exist
            Profile.objects.create(user=instance)
            print("Profile was not exist, but I create one")
        print('User is updated')