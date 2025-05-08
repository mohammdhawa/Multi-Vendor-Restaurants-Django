from django import forms
from .models import Category, FoodItem
from accounts.validators import allow_only_images_validator


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('category_name', 'description')


class FoodItemForm(forms.ModelForm):
    image = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'btn btn-info w-100'}),
        validators=[allow_only_images_validator]
    )

    class Meta:
        model = FoodItem
        fields = ('category', 'food_title', 'description', 'price', 'image', 'is_available')

    def __init__(self, *args, **kwargs):
        vendor = kwargs.pop('vendor', None)  # Get vendor from kwargs
        super(FoodItemForm, self).__init__(*args, **kwargs)
        if vendor:
            self.fields['category'].queryset = Category.objects.filter(vendor=vendor)

