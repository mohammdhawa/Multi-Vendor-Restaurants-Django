from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect

from menue.models import Category
from .forms import VendorForm, UserProfileForm
from accounts.models import Profile
from .models import Vendor
from menue.models import Category, FoodItem
from accounts.views import check_role_vendor
from menue.forms import CategoryForm, FoodItemForm


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
