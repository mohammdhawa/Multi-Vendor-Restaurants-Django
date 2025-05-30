from django.urls import path, include
from . import views
from project.views import home


urlpatterns = [
    # path('my-account/', views.my_account, name='my-account'),
    path('registerUser', views.register_user, name='register-user'),
    path('registerVendor', views.register_vendor, name='register-vendor'),

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('my-account/', views.my_account, name='my-account'),
    path('customer-dashboard/', views.customer_dashboard, name='customer-dashboard'),
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor-dashboard'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password-validate/<uidb64>/<token>/', views.reset_password_validate, name='reset-password-validate'),
    path('reset-password/', views.reset_password, name='reset-password'),

    path('vendor/', include('vendor.urls')),
    path('customer/', include('customers.urls')),
]
