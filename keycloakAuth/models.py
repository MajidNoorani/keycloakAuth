from django.db import models
import os
import uuid
from django.utils import timezone


# Create your models here.
def user_profile_picture_file_path(instance, filename):
    """Generate file path for new post category image"""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'user_profile_picture', filename)


class UserProfile(models.Model):
    """User in the system"""
    uuid = models.CharField(primary_key=True,
                            unique=True,
                            max_length=255)
    email = models.EmailField(unique=True)
    profilePicture = models.ImageField(
        null=True,
        blank=True,
        upload_to=user_profile_picture_file_path)
    createdDate = models.DateTimeField(
        default=timezone.now,
        verbose_name="Created Date"
        )
    updatedDate = models.DateTimeField(
        default=None,
        null=True
        )
