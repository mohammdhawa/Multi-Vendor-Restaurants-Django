from django.db import models
from accounts.models import User
from menue.models import FoodItem


class Cart(models.Model):
    user = models.ForeignKey(User, related_name='cart_user', on_delete=models.CASCADE)
    fooditem = models.ForeignKey(FoodItem, related_name='cart_fooditem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.user)
