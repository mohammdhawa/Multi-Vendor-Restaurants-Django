from project import settings
from vendor.models import Vendor
from accounts.models import Profile
from orders.models import Order, OrderFood, FoodItem

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


def get_paypal_client_id(request):
    return {'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID}

def get_stripe_publishable_key(request):
    return {'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY}


def food_data(request):
    order_foods = OrderFood.objects.filter(
        user=request.user,
        order__is_ordered=True,
        order__status='Completed'  # Optional: only include completed orders
    )

    # Build response in desired format
    data = [
        {
            "fooditem": item.fooditem.food_title,
            "category": item.fooditem.category.category_name,
            "description": item.fooditem.description,
            "quantity": item.quantity
        }
        for item in order_foods
    ]


    all_fooditems = FoodItem.objects.all()

    data2 = [
        {
            "id": item.id,
            "fooditem": item.food_title,
            "category": item.category.category_name,
            "description": item.description,
        }
        for item in all_fooditems
    ]

    context = {
        'prev_fooditems': data,
        'all_fooditems': data2,
    }

    return context