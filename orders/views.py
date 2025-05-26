from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from marketplace.models import Cart
from orders.forms import OrderForm
from orders.models import Order, OrderFood
from .utils import generate_order_number, generate_order_no
from django.contrib import messages


@login_required(login_url='login')
@require_POST
def place_order(request):
    """
    This view now only validates the form and stores order data in session.
    The actual order creation happens after successful payment.
    """
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('marketplace')

    form = OrderForm(request.POST)
    if form.is_valid():
        # Store order data in session for later use after payment
        request.session['pending_order'] = {
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
            'email': form.cleaned_data['email'],
            'address': form.cleaned_data['address'],
            'city': form.cleaned_data['city'],
            'state': form.cleaned_data['state'],
            'postal_code': form.cleaned_data['postal_code'],
            'phone': form.cleaned_data['phone'],
            'country': form.cleaned_data['country'],
            'payment_method': request.POST.get('payment_method', 'stripe'),
        }

        # Redirect to payment page instead of creating order
        return redirect('payment_page')
    else:
        # If form is invalid, redirect back to checkout with errors
        messages.error(request, 'Please correct the errors in your form.')
        return redirect('checkout')


def order_complete(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, user=request.user, is_ordered=True)
        ordered_food = OrderFood.objects.filter(order=order)

        # Calculate subtotal from ordered items
        subtotal = sum(item.amount for item in ordered_food)

        # Clear the order_id from session
        if 'order_id' in request.session:
            del request.session['order_id']

        context = {
            'order': order,
            'ordered_food': ordered_food,
            'subtotal': subtotal,
        }

        return render(request, 'orders/order_complete.html', context)

    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('marketplace')
