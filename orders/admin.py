from django.contrib import admin
from .models import Payment, Order, OrderFood


admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(OrderFood)
