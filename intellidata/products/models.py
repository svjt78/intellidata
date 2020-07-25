from django.conf import settings
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.utils.text import slugify

from sorl.thumbnail import ImageField
import misaka

from django.contrib.auth import get_user_model

# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
#from products.serializers import ProductSerializer
import requests

User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template
register = template.Library()

class Product(models.Model):
    productid = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    CHOOSE = 'Unknown Type'
    LIFE = 'LIFE'
    STD = 'STD'
    LTD = 'LTD'
    CI = 'CI'
    PRODUCT_CHOICES = (
        (CHOOSE, 'Unknown Type'),
        (LIFE, 'Life Insurance'),
        (STD, 'Short Term Disability'),
        (LTD, 'Long Term Disability'),
        (CI, 'Critical Illness'),
    )
    type = models.CharField(max_length=100,
                                      choices=PRODUCT_CHOICES,
                                      default=CHOOSE)

    slug = models.SlugField(allow_unicode=True)
    description = models.TextField(blank=True, default='')
    description_html = models.TextField(editable=False, default='', blank=True)
    #coverage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coverage_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_per_1000_units = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product_date = models.DateTimeField(auto_now=True)
    photo = models.ImageField(blank=True, null=True)
    backend_SOR_connection = models.CharField(max_length=255, default='Disconnected')
    transaction_status = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return ("Name: "+self.name + "~" + "Type: "+self.type + "~" + "Coverage limit: "+ str(self.coverage_limit) + "~" + "Created on: "+self.product_date.strftime("%d-%b-%Y (%H:%M:%S.%f)"))

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self.description_html = misaka.html(self.description)
        self.transaction_status='Success'
        super().save(*args, **kwargs)

        #connect to backend
        if self.backend_SOR_connection != "Disconnected":
            #converty model object to json
            serializer = ProductSerializer(self)
            json_data = serializer.data
            url='https://brnmd9qrbk.execute-api.us-east-1.amazonaws.com/prod/intellidataProductAPI/base1/nrt'
            #post data to the API for backend connection
            resp = requests.post(url, json=json_data)
            if resp.status_code != 201:
                #raise APIError(resp.status_code)
                self.transaction_status="Data posting failed with " + str(resp.status_code)
            else:
                self.transaction_status="Data posting successful with " + str(resp.status_code)
            super().save(*args, **kwargs)
        else:
            print("not connecting to backend!")


    def get_absolute_url(self):
        return reverse("products:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-product_date"]
        unique_together = ("name", "type", "product_date")


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
