from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from menue.models import Category
from .forms import VendorForm, UserProfileForm
from accounts.models import Profile
from .models import Vendor
from menue.models import Category, FoodItem
from accounts.views import check_role_vendor
from menue.forms import CategoryForm, FoodItemForm
from orders.models import Order, OrderFood
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate, TruncMonth
import calendar
from django.db.models import F, FloatField, Sum


def get_vendor(request):
    vendor = Vendor.objects.get(user=request.user)
    return vendor


@login_required
@user_passes_test(check_role_vendor)
def vprofile(request):
    profile = get_object_or_404(Profile, user=request.user)
    vendor = get_vendor(request)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        vendor_form = VendorForm(request.POST, request.FILES, instance=vendor)
        if profile_form.is_valid() and vendor_form.is_valid():
            profile_form.save()
            vendor_form.save()
            messages.success(request, 'Settings updated successfully')
            return redirect('vprofile')
        else:
            print(profile_form.errors)
            print(vendor_form.errors)
    else:
        vendor_form = VendorForm(instance=vendor)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'vendor_form': vendor_form,
        'profile_form': profile_form,
        'profile': profile,
        'vendor': vendor
    }
    return render(request, 'vendor/vprofile.html', context)


@login_required
@user_passes_test(check_role_vendor)
def menu_builder(request):
    vendor = get_vendor(request)
    categories = Category.objects.filter(vendor=vendor)

    context = {
        'categories': categories,
        # 'vendor': vendor,
    }

    return render(request, 'vendor/menu_builder.html', context)


@login_required
@user_passes_test(check_role_vendor)
def fooditems_by_category(request, pk=None):
    vendor = get_vendor(request)
    category = get_object_or_404(Category, pk=pk)
    fooditems = FoodItem.objects.filter(category=category)

    context = {
        'fooditems': fooditems,
        'category': category,
        'vendor': vendor,
    }

    return render(request, 'vendor/fooditems_by_category.html', context)


@login_required
@user_passes_test(check_role_vendor)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.vendor = get_vendor(request)
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('menu-builder')
        else:
            pass
    else:
        form = CategoryForm()

    context = {
        'form': form
    }
    return render(request, 'vendor/add_category.html', context)


@login_required
@user_passes_test(check_role_vendor)
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, vendor=get_vendor(request))

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('menu-builder')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category
    }
    return render(request, 'vendor/edit_category.html', context)


@login_required
@user_passes_test(check_role_vendor)
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, vendor=get_vendor(request))
    category.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('menu-builder')


@login_required
@user_passes_test(check_role_vendor)
def add_fooditem(request):
    vendor = get_vendor(request)  # Make sure this returns the correct vendor instance

    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, vendor=vendor)
        if form.is_valid():
            fooditem = form.save(commit=False)
            fooditem.vendor = vendor
            fooditem.save()
            messages.success(request, 'Food item added successfully!')
            return redirect('fooditems_by_category', fooditem.category.id)
        else:
            print(form.errors)
    else:
        form = FoodItemForm(vendor=vendor)

    context = {
        'form': form
    }
    return render(request, 'vendor/add_fooditem.html', context)


@login_required
@user_passes_test(check_role_vendor)
def edit_fooditem(request, pk):
    vendor = get_vendor(request)
    fooditem = get_object_or_404(FoodItem, pk=pk, vendor=vendor)  # Ensure vendor owns the fooditem

    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=fooditem, vendor=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Food item updated successfully!')
            return redirect('fooditems_by_category', fooditem.category.id)
        else:
            print(form.errors)
    else:
        form = FoodItemForm(instance=fooditem, vendor=vendor)

    context = {
        'form': form,
        'food': fooditem
    }
    return render(request, 'vendor/edit_fooditem.html', context)


@login_required
@user_passes_test(check_role_vendor)
def delete_fooditem(request, pk):
    vendor = get_vendor(request)
    fooditem = get_object_or_404(FoodItem, pk=pk, vendor=vendor)  # Ensures ownership
    category = fooditem.category

    fooditem.delete()
    messages.success(request, 'Food item deleted successfully!')
    return redirect('fooditems_by_category', category.id)  # Or wherever you list the vendor's food items


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendor_orders(request):
    """Display all orders for the current vendor"""
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "You don't have a vendor account.")
        return redirect('dashboard')

    # Get all orders that contain food items from this vendor
    orders = Order.objects.filter(
        order_food__fooditem__vendor=vendor,
        is_ordered=True
    ).distinct().order_by('-created_at')

    # Add vendor totals to each order
    for order in orders:
        vendor_total = order.get_total_by_vendor(vendor.id)
        order.vendor_total = vendor_total['grand_total']

    context = {
        'orders': orders,
        'vendor': vendor,
        'status_choices': Order.STATUS,  # Pass status choices to template
    }
    return render(request, 'vendor/vendor_orders.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendor_orders(request):
    """Display all orders for the current vendor"""
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "You don't have a vendor account.")
        return redirect('dashboard')

    # Get all orders that contain food items from this vendor
    orders = Order.objects.filter(
        order_food__fooditem__vendor=vendor,
        is_ordered=True
    ).distinct().order_by('-created_at')

    # Add vendor totals to each order
    for order in orders:
        vendor_total = order.get_total_by_vendor(vendor.id)
        order.vendor_total = vendor_total['grand_total']

    context = {
        'orders': orders,
        'vendor': vendor,
        'status_choices': Order.STATUS,  # Add status choices for the form
    }
    return render(request, 'vendor/vendor_orders.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendor_order_detail(request, order_number):
    """Display detailed view of a specific order for vendor"""
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "You don't have a vendor account.")
        return redirect('dashboard')

    # Get the order and verify it contains items from this vendor
    order = get_object_or_404(Order, order_number=order_number, is_ordered=True)

    # Get only the food items from this vendor in this order
    ordered_food = OrderFood.objects.filter(
        order=order,
        fooditem__vendor=vendor
    ).select_related('fooditem')

    if not ordered_food.exists():
        messages.error(request, "You don't have access to this order.")
        return redirect('vendor_orders')

    # Add vendor total to order
    order.get_total_by_vendor = order.get_total_by_vendor(vendor.id)

    context = {
        'order': order,
        'ordered_food': ordered_food,
        'vendor': vendor,
    }
    return render(request, 'vendor/vendor_order_detail.html', context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
@require_POST
@csrf_exempt
def update_order_status(request):
    """Update order status via AJAX"""
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        return JsonResponse({'success': False, 'message': "You don't have a vendor account."})

    if request.method == 'POST':
        data = json.loads(request.body)
        order_number = data.get('order_number')
        new_status = data.get('status')

        try:
            # Get the order and verify it belongs to this vendor
            order = Order.objects.filter(
                order_number=order_number,
                order_food__fooditem__vendor=vendor,
                is_ordered=True
            ).distinct().first()

            if not order:
                return JsonResponse({'success': False, 'message': 'Order not found or not accessible'})

            # Validate status
            valid_statuses = [choice[0] for choice in Order.STATUS]
            if new_status not in valid_statuses:
                return JsonResponse({'success': False, 'message': 'Invalid status'})

            # Update the status
            order.status = new_status
            order.save()

            return JsonResponse({
                'success': True,
                'message': f'Order {order_number} status updated to {new_status}',
                'new_status': new_status
            })

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendor_earnings(request):
    """Display earnings analytics for the vendor"""
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "You don't have a vendor account.")
        return redirect('dashboard')

    # Get date filters from request
    period = request.GET.get('period', 'this_month')

    # Calculate date ranges
    today = timezone.now().date()

    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'last_month':
        first_day_this_month = today.replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        # Default to this month
        start_date = today.replace(day=1)
        end_date = today

    # Filter orders for the vendor within date range
    vendor_orders = Order.objects.filter(
        order_food__fooditem__vendor=vendor,
        is_ordered=True,
        created_at__date__range=[start_date, end_date]
    ).distinct()

    # Calculate total earnings
    total_earnings = 0
    total_orders = vendor_orders.count()
    total_food_items_sold = 0

    earnings_by_order = []

    for order in vendor_orders:
        vendor_total_data = order.get_total_by_vendor(vendor.id)
        vendor_earnings = vendor_total_data['grand_total']
        total_earnings += vendor_earnings

        # Count food items sold in this order
        food_items_count = OrderFood.objects.filter(
            order=order,
            fooditem__vendor=vendor
        ).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
        total_food_items_sold += food_items_count

        earnings_by_order.append({
            'order': order,
            'earnings': vendor_earnings,
            'items_count': food_items_count
        })

    # Calculate average order value
    avg_order_value = total_earnings / total_orders if total_orders > 0 else 0

    # Get top selling food items
    top_food_items = OrderFood.objects.filter(
        order__in=vendor_orders,
        fooditem__vendor=vendor
    ).values(
        'fooditem__food_title',
        'fooditem__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('quantity') * Sum('fooditem__price')
    ).order_by('-total_quantity')[:5]

    # Monthly earnings for chart (last 6 months)
    monthly_earnings = []
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        month_orders = Order.objects.filter(
            order_food__fooditem__vendor=vendor,
            is_ordered=True,
            created_at__date__range=[month_start, month_end]
        ).distinct()

        month_total = 0
        for order in month_orders:
            month_total += order.get_total_by_vendor(vendor.id)['grand_total']

        monthly_earnings.append({
            'month': calendar.month_name[month_start.month],
            'year': month_start.year,
            'earnings': month_total
        })

    monthly_earnings.reverse()  # Show oldest to newest

    # Recent transactions (last 10)
    recent_orders = vendor_orders.order_by('-created_at')[:10]
    recent_transactions = []
    for order in recent_orders:
        vendor_total_data = order.get_total_by_vendor(vendor.id)
        recent_transactions.append({
            'order': order,
            'earnings': vendor_total_data['grand_total'],
            'date': order.created_at
        })

    context = {
        'vendor': vendor,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_earnings': total_earnings,
        'total_orders': total_orders,
        'total_food_items_sold': total_food_items_sold,
        'avg_order_value': avg_order_value,
        'top_food_items': top_food_items,
        'monthly_earnings': monthly_earnings,
        'recent_transactions': recent_transactions,
        'earnings_by_order': earnings_by_order,
    }

    return render(request, 'vendor/vendor_earnings.html', context)