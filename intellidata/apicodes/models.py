from django.conf import settings
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.shortcuts import get_object_or_404, render
import requests

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template
register = template.Library()

class APICodes(models.Model):

    STANDARD = 'Standard'
    CUSTOM = 'Custom'

    CODE_CHOICES = (
        (STANDARD, 'Standard'),
        (CUSTOM, 'Custom')
    )

    http_error_category = models.TextField(blank=True, null=True)
    http_response_code = models.TextField(unique=True)
    http_response_message = models.TextField(blank=True, null=True)
    API_code_type = models.CharField(max_length=100,
                                      choices=CODE_CHOICES,
                                      default=STANDARD)


    def __str__(self):
        return self.http_response_message

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("apicodes:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["http_response_code"]
