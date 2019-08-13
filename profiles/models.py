from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(
        default="profile_pics/default_user.jpg", upload_to='profile_pics')
    flow_units = models.CharField(
        max_length=20, blank=True, null=True, default="Gallons per minute")
    head_units = models.CharField(
        max_length=20, blank=True, null=True, default="Feet")
    power_units = models.CharField(
        max_length=20, blank=True, null=True, default="Horsepower")

    def __str__(self):
        return f'{self.user.username} Profile'
