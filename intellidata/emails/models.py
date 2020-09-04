from django.conf import settings
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.shortcuts import get_object_or_404, render
import requests
from employers.models import Employer

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template
register = template.Library()

class Email(models.Model):

    PLANADMIN = 'Plan Admin'
    ADMINISTRATOR = 'Administrator'

    CODE_CHOICES = (
        (PLANADMIN, 'Plan Admin'),
        (ADMINISTRATOR, 'Administrator')
    )

    employer = models.ForeignKey(Employer, on_delete=models.SET_NULL, null=True, blank=True, related_name="planadmin_set")

    role = models.CharField(max_length=100,
                                      choices=CODE_CHOICES,
                                      default=PLANADMIN)

    emailaddress  = models.EmailField(max_length=254)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="operator_set")
    create_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.emailaddress

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("emails:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-create_date"]
