from .models import Cart
from menue.models import FoodItem


def get_cart_count(request):
    cart_count = 0

    if request.user.is_authenticated:
        try:
            cart_items = Cart.objects.filter(user=request.user)
            if cart_items:
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
        except:
            cart_count = 0
    return dict(
        cart_count = cart_count
    )