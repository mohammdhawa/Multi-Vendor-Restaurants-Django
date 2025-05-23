from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from vendor.forms import UserProfileForm
from accounts.forms import UserInfoForm
from accounts.models import Profile
from django.contrib import messages


@login_required(login_url='login')
def cprofile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        user_form = UserInfoForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Profile Updated Successfully!')
            return redirect('cprofile')
    else:
        profile_form = UserProfileForm(instance=profile)
        user_form = UserInfoForm(instance=request.user)

    context = {
        'profile_form': profile_form,
        'user_form': user_form,
        'profile': profile
    }
    return render(request, 'customers/cprofile.html', context)
