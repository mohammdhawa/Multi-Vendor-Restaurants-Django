from django import forms
from .models import Vendor
from accounts.models import Profile
from accounts.validators import allow_only_images_validator


class VendorForm(forms.ModelForm):
    vendor_license = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}), validators=[allow_only_images_validator])
    class Meta:
        model = Vendor
        fields = ('vendor_name', 'vendor_license')


class UserProfileForm(forms.ModelForm):
    address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Start typing ...', 'required': 'required',}))
    profile_picture = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}), validators=[allow_only_images_validator])
    cover_picture = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}), validators=[allow_only_images_validator])

    # latitude = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    # longitude = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    class Meta:
        model = Profile
        exclude = ('user', 'created_at', 'modified_at')

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'latitude' or field == 'longitude':
                self.fields[field].widget.attrs['readonly'] = 'readonly'
