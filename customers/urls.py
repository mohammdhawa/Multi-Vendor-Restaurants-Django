from django.urls import path
from accounts import views as AccountViews
from . import views


urlpatterns = [
    path('', AccountViews.customer_dashboard, name='customer'),
    path('profile/', views.cprofile, name='cprofile'),
    path('my-orders/', views.my_orders, name='my-orders'),
    path('order-detail/<str:order_number>/', views.order_detail, name='order-detail'),
]