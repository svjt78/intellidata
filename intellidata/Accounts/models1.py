from django.contrib import auth
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Group


class User(auth.models.User, auth.models.PermissionsMixin,):

    def __str__(self):
        return "@{}".format(self.username)


    def save(self, *args, **kwargs):
        print("I am here")
        print("User:" + self.username)

        if (self.username == "super"):
            self.groups.add(Group.objects.get(name='administrator'))
        else:
            self.groups.add(Group.objects.get(name='appuser'))

        super().save(*args, **kwargs)
