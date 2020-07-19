from django.conf import settings
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.utils.text import slugify

import misaka

from django.contrib.auth import get_user_model
User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template
register = template.Library()

class BulkUpload(models.Model):

    file = models.FileField(blank=True, null=True)
    createdate = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')
    description_html = models.TextField(editable=False, default='', blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.description_html = misaka.html(self.description)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return render(request, "test.html", {"filemessage": "File uploaded succesfully"})

    class Meta:
        ordering = ["-createdate"]
