from django.urls import path
from . import views


urlpatterns = [
    path('registerUser', views.register_user, name='register-user'),
    path('registerVendor', views.register_vendor, name='register-vendor'),

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('my-account/', views.my_account, name='my-account'),
    path('customer-dashboard/', views.customer_dashboard, name='customer-dashboard'),
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor-dashboard'),
]
