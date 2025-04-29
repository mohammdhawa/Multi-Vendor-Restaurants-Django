from django.urls import path
from . import views


urlpatterns = [
    path('registerUser', views.register_user, name='register-user'),
    path('registerVendor', views.register_vendor, name='register-vendor'),
]
