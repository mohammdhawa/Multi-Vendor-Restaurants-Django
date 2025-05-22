from django.shortcuts import render, get_object_or_404, redirect
from vendor.models import Vendor
from menue.models import Category, FoodItem
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse

from .context_processors import get_cart_count
from .models import Cart
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D # D = Distance
from django.contrib.gis.db.models.functions import Distance


def marketplace(reqeust):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()

    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(reqeust, 'marketplace/listings.html', context)


def vendor_detail(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug)
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch('category_food_item', queryset=FoodItem.objects.filter(is_available=True))
    )

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        print('Cart items:')
        print(cart_items)
    else:
        cart_items = None
    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def cart(request):
    """
    Display the cart page with all cart items for the logged-in user
    """
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)

        # Calculate subtotal and grand total
        subtotal = 0
        for item in cart_items:
            subtotal += (item.fooditem.price * item.quantity)

        # Grand total is same as subtotal since we're not using taxes
        grand_total = subtotal

        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'grand_total': grand_total,
        }
        return render(request, 'marketplace/cart.html', context)
    else:
        return redirect('login')


def add_to_cart(request, food_id=None):
    """
    Add a food item to the cart or increase its quantity
    """
    if request.user.is_authenticated:
        # Checking if the request is ajax request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the fooditem exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)

                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    # Increase the cart quantity
                    chkCart.quantity += 1
                    chkCart.save()

                    # Calculate new subtotal and grand total
                    cart_items = Cart.objects.filter(user=request.user)
                    subtotal = 0
                    for item in cart_items:
                        subtotal += (item.fooditem.price * item.quantity)
                    grand_total = subtotal  # No taxes

                    return JsonResponse({
                        'status': 'Success',
                        'message': 'Food added to cart successfully',
                        'cart_counter': get_cart_count(request),
                        'quantity': chkCart.quantity,  # Return updated quantity
                        'subtotal': subtotal,
                        'grand_total': grand_total
                    })
                except:
                    chkCart = Cart.objects.create(user=request.user, fooditem=fooditem, quantity=1)
                    chkCart.save()

                    # Calculate new subtotal and grand total
                    cart_items = Cart.objects.filter(user=request.user)
                    subtotal = 0
                    for item in cart_items:
                        subtotal += (item.fooditem.price * item.quantity)
                    grand_total = subtotal  # No taxes

                    return JsonResponse({
                        'status': 'Success',
                        'message': 'Added the food to the cart!',
                        'cart_counter': get_cart_count(request),
                        'quantity': chkCart.quantity,  # Return initial quantity
                        'subtotal': subtotal,
                        'grand_total': grand_total
                    })
            except:
                return JsonResponse({'status': 'Failed', 'message': "This food doesn't exist"})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request!'})
    return JsonResponse({
        'status': 'Failed',
        'message': 'Please login to continue!'
    })


def decrease_cart(request, food_id=None):
    """
    Decrease the quantity of a food item in the cart
    """
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if chkCart.quantity > 1:
                        chkCart.quantity -= 1
                        chkCart.save()

                        # Calculate new subtotal and grand total
                        cart_items = Cart.objects.filter(user=request.user)
                        subtotal = 0
                        for item in cart_items:
                            subtotal += (item.fooditem.price * item.quantity)
                        grand_total = subtotal  # No taxes

                        return JsonResponse({
                            'status': 'Success',
                            'message': 'Cart quantity decreased successfully',
                            'cart_counter': get_cart_count(request),
                            'quantity': chkCart.quantity,
                            'subtotal': subtotal,
                            'grand_total': grand_total
                        })
                    else:
                        cart_id = chkCart.id
                        chkCart.delete()  # Remove item if quantity becomes 0

                        # Calculate new subtotal and grand total
                        cart_items = Cart.objects.filter(user=request.user)
                        subtotal = 0
                        for item in cart_items:
                            subtotal += (item.fooditem.price * item.quantity)
                        grand_total = subtotal  # No taxes

                        return JsonResponse({
                            'status': 'Success',
                            'message': 'Item removed from cart',
                            'cart_counter': get_cart_count(request),
                            'quantity': 0,
                            'cart_id': cart_id,
                            'subtotal': subtotal,
                            'grand_total': grand_total
                        })
                except Cart.DoesNotExist:
                    return JsonResponse({
                        'status': 'Failed',
                        'message': 'This item is not in your cart'
                    })
            except FoodItem.DoesNotExist:
                return JsonResponse({
                    'status': 'Failed',
                    'message': 'This food does not exist'
                })
        else:
            return JsonResponse({
                'status': 'Failed',
                'message': 'Invalid request!'
            })
    return JsonResponse({
        'status': 'Failed',
        'message': 'Please login to continue!'
    })


def delete_cart(request, cart_id=None):
    """
    Delete a cart item completely - Simplified and robust version
    """
    # Print debugging information
    print(f"Delete cart request received for cart_id: {cart_id}")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"Is AJAX request: {request.headers.get('x-requested-with') == 'XMLHttpRequest'}")

    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'Failed',
            'message': 'Please login to continue!'
        })

    # Check if it's an AJAX request
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({
            'status': 'Failed',
            'message': 'Invalid request!'
        })

    # Get the cart item
    try:
        cart_item = Cart.objects.get(id=cart_id)

        # Check if the cart item belongs to the logged-in user
        if cart_item.user != request.user:
            return JsonResponse({
                'status': 'Failed',
                'message': 'You are not authorized to delete this cart item!'
            })

        # Delete the cart item
        cart_item.delete()
        print(f"Cart item {cart_id} deleted successfully")

        # Calculate new totals
        cart_items = Cart.objects.filter(user=request.user)
        subtotal = sum(item.fooditem.price * item.quantity for item in cart_items)
        grand_total = subtotal  # No taxes

        return JsonResponse({
            'status': 'Success',
            'message': 'Cart item has been deleted!',
            'cart_counter': get_cart_count(request),
            'subtotal': subtotal,
            'grand_total': grand_total
        })

    except Cart.DoesNotExist:
        print(f"Cart item {cart_id} not found")
        return JsonResponse({
            'status': 'Failed',
            'message': 'Cart item does not exist!'
        })
    except Exception as e:
        print(f"Error deleting cart item: {str(e)}")
        return JsonResponse({
            'status': 'Failed',
            'message': f'Error: {str(e)}'
        })


def search(request):
    if not 'address' in request.GET:
        return redirect('marketplace')
    else:
        address = request.GET.get('address')
        latitude = request.GET.get('lat')
        longitude = request.GET.get('lng')
        radius = request.GET.get('radius')
        keyword = request.GET.get('keyword')

        # get vendors ids that has food item the user is looking for
        fetch_vendors_by_fooditems = FoodItem.objects.filter(
            food_title__icontains=keyword,
            is_available=True
        ).values_list('vendor', flat=True)

        # Build the base query with keyword filtering
        vendors = Vendor.objects.filter(
            Q(id__in=fetch_vendors_by_fooditems) |
            Q(vendor_name__icontains=keyword),
            is_approved=True,
            user__is_active=True
        )

        # Add location filter if coordinates and radius are provided
        if latitude and longitude and radius:
            try:
                # Convert to float to ensure valid data
                lat_float = float(latitude)
                lng_float = float(longitude)
                radius_float = float(radius)

                # Create the point from coordinates
                pnt = GEOSGeometry(f'POINT({lng_float} {lat_float})')

                # Refine the existing query with the location filter
                vendors = vendors.filter(
                    Q(id__in=fetch_vendors_by_fooditems) |
                    Q(vendor_name__icontains=keyword),
                    is_approved=True,
                    user__is_active=True,
                    user_profile__location__distance_lte=(pnt, D(km=radius_float))
                ).annotate(distance=Distance('user_profile__location', pnt)).order_by('distance')

                for v in vendors:
                    v.kms = round(v.distance.km, 1)


                print("Result After location filtering: ", vendors)

                print(f"Location search with point {pnt} and radius {radius_float}km")
                print(latitude, longitude)
            except (ValueError, TypeError) as e:
                # Log error if coordinates aren't valid
                print(f"Error in location filtering: {e}")

        vendor_count = vendors.count()
        print(f"Found {vendor_count} vendors matching the criteria")

        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'source_location': address,

        }
        return render(request, 'marketplace/listings.html', context)
