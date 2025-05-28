from django.db import models
from accounts.models import User
from menue.models import FoodItem


class Payment(models.Model):
    PAYMENT_METHOD = (
        ('PayPal', 'PayPal'),
    )
    user = models.ForeignKey(User, related_name='user_payment', on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD)
    amount = models.CharField(max_length=10)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, related_name='user_order', on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, related_name='payment_order', on_delete=models.SET_NULL, null=True, blank=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=200)
    country = models.CharField(max_length=25, blank=True)
    state = models.CharField(max_length=25, blank=True)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    order_note = models.CharField(max_length=100, blank=True, null=True)
    total = models.FloatField()
    payment_method = models.CharField(max_length=25)
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    is_ordered = models.BooleanField(default=False)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.order_number

    def get_total_by_vendor(self, vendor_id):
        """Calculate totals for a specific vendor"""
        vendor_items = self.order_food.filter(fooditem__vendor_id=vendor_id)

        if not vendor_items.exists():
            return {
                'subtotal': 0,
                'tax': 0,
                'grand_total': 0
            }

        subtotal = sum(item.amount for item in vendor_items)

        # Calculate tax proportionally (assuming 10% tax rate, adjust as needed)
        tax_rate = 0.10
        vendor_tax = subtotal * tax_rate

        return {
            'subtotal': round(subtotal, 2),
            'tax': round(vendor_tax, 2),
            'grand_total': round(subtotal + vendor_tax, 2)
        }


class OrderFood(models.Model):
    order = models.ForeignKey(Order, related_name='order_food', on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, related_name='payment_food', on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(User, related_name='user_food', on_delete=models.CASCADE)
    fooditem = models.ForeignKey(FoodItem, related_name='fooditem_food', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.fooditem.food_title
