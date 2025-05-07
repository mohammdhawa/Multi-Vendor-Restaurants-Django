from django.contrib import admin
from .models import Category, FoodItem


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'vendor', 'id', 'updated_at')
    search_fields = ('category_name', 'vendor__vendor_name')
    ordering = ('-id',)


class FoodItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('food_title',)}
    list_display = ('food_title', 'category', 'id', 'updated_at')
    search_fields = ('food_title', 'category__category_name', 'vendor__vendor_name')
    list_filter = ('is_available', )
    ordering = ('-id',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(FoodItem, FoodItemAdmin)
