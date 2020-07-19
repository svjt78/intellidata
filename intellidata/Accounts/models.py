from django.contrib import auth
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Group


class User(auth.models.User, auth.models.PermissionsMixin,):

    def __str__(self):
        return "@{}".format(self.username)
