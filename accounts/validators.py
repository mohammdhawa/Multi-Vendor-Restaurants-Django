from django.core.exceptions import ValidationError
import os


def allow_only_images_validator(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png']
    print(ext)
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only images with (.jpg, .jpeg and .png) are allowed')