from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_employer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    user_membership = models.OneToOneField('memberships.UserMembership', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username
