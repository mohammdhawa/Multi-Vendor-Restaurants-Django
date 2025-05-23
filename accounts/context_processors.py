from project import settings
from vendor.models import Vendor
from accounts.models import Profile

def get_vendor(request):
    try:
        vendor = Vendor.objects.get(user=request.user)
    except:
        vendor = None

    context = {
        'vendor': vendor,
    }

    return context


def get_user_profile(request):
    try:
        user_profile = Profile.objects.get(user=request.user)
    except:
        user_profile = None

    return dict(
        user_profile = user_profile)


def get_google_api(request):
    return {'GOOGLE_API_KEY': settings.GOOGLE_API_KEY}