from django.contrib import messages
from django.shortcuts import render, redirect

from vendor.forms import VendorForm
from .forms import UserForm
from .models import User


def register_user(request):

    if request.method == 'POST':
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
    userForm = UserForm()
    vendorForm = VendorForm()

    if request.method == 'POST':
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
            user.role = User.RESTAURANT
            user.save()

            vendor = vendorForm.save(commit=False)
            vendor.user = user
            vendor.user_profile = user.profile
            vendor.save()
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