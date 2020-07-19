from django.contrib import auth
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class User(auth.models.User, auth.models.PermissionsMixin, AbstractUser):

        ADMINISTRATOR = 1
        APPUSER = 2

        ROLE_CHOICES = (
            (ADMINISTRATOR, 'Administrator'),
            (APPUSER, 'AppUser'),

        )

        role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True)
        # You can create Role model separately and add ManyToMany if user has more than one role

        def __str__(self):
            return "@{}".format(self.username)
