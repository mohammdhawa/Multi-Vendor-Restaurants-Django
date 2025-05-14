from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.contrib import auth
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode

from .utils import detect_user, send_verification_email, send_reset_password_email

from vendor.forms import VendorForm
from .forms import UserForm
from .models import User
from vendor.models import Vendor


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

    return render(request, 'accounts/customerDashboard.html', {})


@login_required
@user_passes_test(check_role_vendor)
def vendor_dashboard(request):

    return render(request, 'accounts/vendorDashboard.html')


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