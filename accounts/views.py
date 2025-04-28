from django.contrib import messages
from django.shortcuts import render, redirect
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
