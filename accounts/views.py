from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode

from menue.models import FoodItem
from .utils import detect_user, send_verification_email, send_reset_password_email

from vendor.forms import VendorForm
from .forms import UserForm
from .models import User
from vendor.models import Vendor
from orders.models import Order, OrderFood
from django.db.models import Sum


# Restrict the vendor from accessing the customer dashboard
def check_role_vendor(user):
    if user.role == 1:
        return True
    raise PermissionDenied

# Restrict the customer from accessing the vendor dashboard
def check_role_customer(user):
    if user.role == 2:
        return True
    raise PermissionDenied

def register_user(request):
    if request.user.is_authenticated:
        messages.success(request, 'You are already logged in')
        return my_account(request)
    elif request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # user = form.save(commit=False)
            # user.set_password(form.cleaned_data['password'])
            # user.role = User.CUSTOMER
            # user.save()

            # Create the user using create_user method in User model
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email,
                                            username=username, password=password)
            user.role = User.CUSTOMER
            user.save()

            # Send verification email to the user
            send_verification_email(request, user)

            messages.success(request, 'Account created successfully')
            return redirect('register-user')
        else:
            print('Invalid form')
            print(form.errors)
    else:
        form = UserForm()

    context = {'form': form}

    return render(request, 'accounts/registerUser.html', context)


def register_vendor(request):
    if request.user.is_authenticated:
        messages.success(request, 'You are already logged in')
        return my_account(request)
    elif request.method == 'POST':
        userForm = UserForm(request.POST)
        vendorForm = VendorForm(request.POST, request.FILES)
        if userForm.is_valid() and vendorForm.is_valid():
            first_name = userForm.cleaned_data['first_name']
            last_name = userForm.cleaned_data['last_name']
            email = userForm.cleaned_data['email']
            username = userForm.cleaned_data['username']
            password = userForm.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email,
                                          username=username, password=password)
            user.role = User.VENDOR
            user.save()

            vendor = vendorForm.save(commit=False)
            vendor.user = user
            vendor.user_profile = user.profile
            vendor.save()

            # Send verification email to the user
            send_verification_email(request, user)

            messages.success(request, 'Your account has beed created successfully! Please wait for approval.')
            return redirect('register-vendor')
    else:
        userForm = UserForm()
        vendorForm = VendorForm()


    context = {
        'userForm': userForm,
        'vendorForm': vendorForm
    }
    return render(request, 'accounts/registerVendor.html', context)


def login(request):
    if request.user.is_authenticated:
        messages.success(request, 'You are already logged in')
        return my_account(request)
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'Login successful')
            return my_account(request)
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

    context = {}
    return render(request, 'accounts/login.html', context)


@login_required
def logout(request):
    auth.logout(request)
    messages.success(request, 'Logout successful')
    return redirect('login')


@login_required
@user_passes_test(check_role_customer)
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True)
    orders_count = orders.count()
    recent_orders = orders.order_by('-created_at')[:3]

    context = {
        'orders_count': orders_count,
        'recent_orders': recent_orders,
    }

    return render(request, 'accounts/customerDashboard.html', context)


@login_required
@user_passes_test(check_role_vendor)
def vendor_dashboard(request):
    """Display vendor dashboard with overview statistics and recent orders"""
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        messages.error(request, "You don't have a vendor account.")
        return redirect('dashboard')

    # Get all orders that contain food items from this vendor
    vendor_orders = Order.objects.filter(
        order_food__fooditem__vendor=vendor,
        is_ordered=True
    ).distinct()

    # Calculate total orders count
    total_orders = vendor_orders.count()

    # Calculate total revenue for this vendor across all orders
    total_revenue = 0
    for order in vendor_orders:
        vendor_total = order.get_total_by_vendor(vendor.id)
        total_revenue += vendor_total['grand_total']

    # Calculate this month's revenue
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_orders = vendor_orders.filter(created_at__gte=current_month_start)

    current_month_revenue = 0
    for order in current_month_orders:
        vendor_total = order.get_total_by_vendor(vendor.id)
        current_month_revenue += vendor_total['grand_total']

    # Get recent orders (last 10 orders)
    recent_orders = vendor_orders.order_by('-created_at')[:10]

    # Add vendor totals to each recent order
    for order in recent_orders:
        vendor_total = order.get_total_by_vendor(vendor.id)
        order.vendor_total = vendor_total['grand_total']
        order.vendor_subtotal = vendor_total['subtotal']
        order.vendor_tax = vendor_total['tax']

        # Calculate charges (assuming it's tax + any service fees)
        order.vendor_charges = vendor_total['tax']

        # Calculate received amount (total - charges)
        order.vendor_received = vendor_total['grand_total'] - vendor_total['tax']

    # Filter orders by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        recent_orders = recent_orders.filter(status=status_filter)

    context = {
        'vendor': vendor,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'current_month_revenue': current_month_revenue,
        'recent_orders': recent_orders,
        'status_choices': Order.STATUS,  # Assuming you have status choices in your Order model
    }

    return render(request, 'accounts/vendorDashboard.html', context)


@login_required
def my_account(request):
    user = request.user
    redirect_url = detect_user(user)

    return redirect(redirect_url)


def activate(request, uidb64, token):
    # Activate the user by setting the is_activate status to True
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated successfully. You can now login.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('login')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            # Send reset password email to the user
            send_reset_password_email(request, user)

            messages.success(request, 'Password reset link has been sent to your email')
            return redirect('login')
        else:
            messages.error(request, 'No account found with that email')
            return redirect('forgot-password')

    return render(request, 'accounts/forgot_password.html')

def reset_password_validate(request, uidb64, token):
    # Validate the user by decoding the token and user pk
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please enter your new password')
        return redirect('reset-password')
    else:
        messages.error(request, 'Reset password link is invalid!')
        return redirect('login')

def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            if uid:
                user = User.objects.get(pk=uid)
                user.set_password(password)
                user.is_active = True
                user.save()
                messages.success(request, 'Password reset successful')
                return redirect('login')
            else:
                messages.error(request, 'Invalid reset password link')
                return redirect('forgot-password')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('reset-password')

    return render(request, 'accounts/reset_password.html')


def chatbot(request):
    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key="d25245ec15514e1db161232d4af35d7e",
    )

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-prover-v2",
            messages=[
                {
                    "role": "user",
                    "content": ''
                }
            ],
            temperature=0.7,
            top_p=0.7,
            frequency_penalty=1,
            max_tokens=512,  # fixed name
        )

        message = response.choices[0].message.content
        print(f"Assistant: {message}")

    except Exception as e:
        print(f"Error during OpenAI call: {e}")
        message = "Something went wrong."

    return render(request, 'home.html', {'response': message})


