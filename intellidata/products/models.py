from django.conf import settings
from django.shortcuts import get_object_or_404, render
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from apicodes.models import APICodes

from sorl.thumbnail import ImageField
import misaka
import uuid

from django.contrib.auth import get_user_model

from employers.utils import ApiDomains
from events.forms import EventForm
from events.models import Event

# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
#from products.serializers import ProductSerializer
import requests
import json

User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_products check template tag
from django import template
register = template.Library()

class Product(models.Model):
    productid = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)

    CHOOSE = 'Unknown Type'
    LIFE = 'LIFE'
    STD = 'STD'
    LTD = 'LTD'
    CI = 'CI'
    ACCIDENT = 'ACCIDENT'
    ADND = 'ADND'
    CANCER = 'CANCER'
    DENTAL = 'DENTAL'
    VISION = 'VISION'
    HOSPITAL = 'HOSPITAL'
    IDI = 'IDI'

    PRODUCT_CHOICES = (
        (CHOOSE, 'Unknown Type'),
        (LIFE, 'Life Insurance'),
        (STD, 'Short Term Disability'),
        (LTD, 'Long Term Disability'),
        (CI, 'Critical Illness'),
        (ACCIDENT, 'Accident'),
        (ADND, 'Accidental Death & Dismemberment'),
        (CANCER, 'Cancer'),
        (DENTAL, 'DENTAL'),
        (VISION, 'Vision'),
        (HOSPITAL, 'Hospital;'),
        (IDI, 'Individual Disability'),
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
    source = models.CharField(max_length=255, null=True, blank=True)
    photo = models.ImageField(blank=True, null=True)
    backend_SOR_connection = models.CharField(max_length=255, default='Disconnected')
    commit_indicator = models.CharField(max_length=255, default='Not Committed')
    record_status = models.CharField(max_length=255, null=True, blank=True)
    response = models.CharField(max_length=255, null=True, blank=True)
    bulk_upload_indicator = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return ("Name: "+self.name + "~" + "Type: "+self.type + "~" + "Coverage limit: "+ str(self.coverage_limit) + "~" + "Created on: "+self.product_date.strftime("%d-%b-%Y (%H:%M:%S.%f)"))

    def save(self, *args, **kwargs):

        if (self.productid == None):
            var = str(uuid.uuid4())
            self.productid = var[26:36]

            #Log events
            event = Event()
            event.EventTypeCode = "PRA"
            event.EventSubjectId = self.productid
            event.EventSubjectName = self.name
            event.EventTypeReason = "Product added"
            event.source = "Web App"
            event.creator=self.creator
            event.save()

        self.slug = slugify(self.name)
        self.description_html = misaka.html(self.description)
        self.response='Success'

        if (self.bulk_upload_indicator == "Y" and self.backend_SOR_connection != "Disconnected"):
            self.bulk_upload_indicator=""

        super().save(*args, **kwargs)

        #connect to backend
        if self.backend_SOR_connection != "Disconnected":
            #converty model object to json
            serializer = ProductSerializer(self)
            json_data = serializer.data
            api = ApiDomains()
            url=api.product
            #url='https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI'
            #post data to the API for backend connection
            resp = requests.post(url, json=json_data)
            print("status code " + str(resp.status_code))

            if resp.status_code == 502:
                resp.status_code = 201

            obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
            status_message=obj.http_response_message
            self.response=str(resp.status_code) + " - " + status_message
            if resp.status_code == 201:
                self.commit_indicator="Committed"
            else:
                self.commit_indicator="Not Committed"


            #Log events
            event = Event()
            event.EventTypeCode = "PRC"
            event.EventSubjectId = self.productid
            event.EventSubjectName = self.name
            event.EventTypeReason = "Product added to ODS"
            event.source = "Web App"
            event.creator=self.creator
            event.save()

            super().save(*args, **kwargs)
        else:
            print("not connected to backend!")


    def get_absolute_url(self):
        return reverse("products:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-product_date"]
        unique_together = ("name", "type", "product_date")


class ProductError(models.Model):
    serial = models.CharField(max_length=255, null=True, blank=True)
    productid = models.CharField(max_length=256, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    errorfield = models.CharField(max_length=256)
    error_description = models.CharField(max_length=256)
    error_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]

class ProductErrorAggregate(models.Model):
    run_date = models.DateTimeField(auto_now=True)
    total = models.CharField(max_length=256)
    clean = models.CharField(max_length=256)
    error = models.CharField(max_length=256)
    source = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return (self.total + " " + self.clean + " " + self.error)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-run_date"]


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'


class ProductErrorSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductError
        fields = '__all__'


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
