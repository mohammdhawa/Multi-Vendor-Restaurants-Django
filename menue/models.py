from django.db import models
from django.utils.text import slugify
from vendor.models import Vendor


class Category(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_category', on_delete=models.CASCADE)
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            self.slug = f"{self.id}-{slugify(self.category_name)}"
            super().save(update_fields=['slug'])

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def clean(self):
        self.category_name = self.category_name.capitalize()


class FoodItem(models.Model):
    vendor = models.ForeignKey(Vendor, related_name='vendor_food_item', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='category_food_item', on_delete=models.CASCADE)
    food_title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='food_item/images')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            self.slug = f"{self.id}-{slugify(self.food_title)}"
            super().save(update_fields=['slug'])

    def __str__(self):
        return self.food_title
