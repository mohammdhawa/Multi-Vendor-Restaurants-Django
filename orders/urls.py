from django.urls import path
from . import views
from marketplace import views as MarketViews


urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),

    # ... your existing URLs
    path('create-stripe-checkout-session/', MarketViews.create_stripe_checkout_session, name='create_stripe_checkout_session'),
    path('payment/success/', MarketViews.payment_success, name='payment_success'),
    path('payment/cancel/', MarketViews.payment_cancel, name='payment_cancel'),
    path('order-complete/<str:order_number>/', views.order_complete, name='order_complete'),
    path('payment/', MarketViews.payment_page, name='payment_page'),
]