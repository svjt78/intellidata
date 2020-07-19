from datetime import datetime
from django.conf import settings
import uuid
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from groups.utils import create_new_ref_number

# from accounts.models import User
from sorl.thumbnail import ImageField
import misaka

from django.contrib.auth import get_user_model
User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template
register = template.Library()



class Group(models.Model):
    groupid = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True)
    description = models.TextField(blank=True, default='')
    description_html = models.TextField(editable=False, default='', blank=True)
    purpose = models.CharField(max_length=255, null=True, default='', blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    group_date = models.DateTimeField(auto_now=True)
    photo = models.ImageField(blank=True, null=True)


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if (self.groupid == None):
            var = str(uuid.uuid4())
            self.groupid = var[26:36]

        self.slug = slugify(self.name)
        self.description_html = misaka.html(self.description)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("groups:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-group_date"]
        unique_together = ("slug", "purpose", "group_date")


class GroupMember(models.Model):
    group = models.ForeignKey(Group, null=True, on_delete=models.SET_NULL, related_name="memberships")
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,related_name='identity')

    def __str__(self):
        return self.user.username

    class Meta:
        unique_together = ("group", "user")
