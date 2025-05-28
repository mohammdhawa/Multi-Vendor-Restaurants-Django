from django.urls import path

from accounts.apps import AccountsConfig
from . import views
from accounts import views as AcouuntViews


urlpatterns = [
    path('', AcouuntViews.vendor_dashboard, name='vendor'),
    path('profile/', views.vprofile, name='vprofile'),
    path('menu-builder/', views.menu_builder, name='menu-builder'),
    path('menu-builder/category/<int:pk>/', views.fooditems_by_category, name='fooditems_by_category'),

    # Category CRUD
    path('menu-builder/category/add', views.add_category, name='add-category'),
    path('menu-builder/category/edit/<int:pk>/', views.edit_category, name='edit-category'),
    path('menu-builder/category/delete/<int:pk>/', views.delete_category, name='delete-category'),

    # FoodItem CRUD
    path('menu-builder/fooditem/add', views.add_fooditem, name='add-fooditem'),
    path('menu-builder/fooditem/edit/<int:pk>/', views.edit_fooditem, name='edit-fooditem'),
    path('menu-builder/fooditem/delete/<int:pk>/', views.delete_fooditem, name='delete-fooditem'),

    path('vendor-orders/', views.vendor_orders, name='vendor_orders'),
    path('order-detail/<str:order_number>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('orders/update-status/', views.update_order_status, name='update_order_status'),
    path('earnings/', views.vendor_earnings, name='vendor_earnings'),
]