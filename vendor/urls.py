from django.urls import path

from accounts.apps import AccountsConfig
from . import views
from accounts import views as AcouuntViews


urlpatterns = [
    path('', AcouuntViews.vendor_dashboard, name='vendor'),
    path('profile/', views.vprofile, name='vprofile'),
]