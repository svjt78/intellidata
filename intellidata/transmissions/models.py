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


# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
#from transmissions.serializers import TransmissionSerializer
import requests
import json

User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_transmissions check template tag
from django import template
register = template.Library()

class Transmission(models.Model):
    transmissionid = models.CharField(max_length=255, null=True, blank=True)
    SenderName = models.CharField(max_length=255, null=True, blank=True)
    BenefitAdministratorPlatform = models.CharField(max_length=255, null=True, blank=True)
    ReceiverName = models.CharField(max_length=255, null=True, blank=True)

    TestProductionCode = models.CharField(max_length=255, null=True, blank=True)
    TransmissionTypeCode = models.CharField(max_length=255, default="Electronic")
    SystemVersionIdentifier = models.CharField(max_length=255, null=True, blank=True)
    source = models.CharField(max_length=1, null=True, blank=True)

    create_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    backend_SOR_connection = models.CharField(max_length=255, default='Disconnected')
    commit_indicator = models.CharField(max_length=255, default='Not Committed')
    record_status = models.CharField(max_length=255, null=True, blank=True)
    response = models.CharField(max_length=255, null=True, blank=True)
    bulk_upload_indicator = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return (self.SenderName)

    def save(self, *args, **kwargs):

        if (self.transmissionid == None):
            var = str(uuid.uuid4())
            self.transmissionid = var[26:36]

        self.response='Success'
        super().save(*args, **kwargs)

        #connect to backend
        if self.backend_SOR_connection != "Disconnected":
            #converty model object to json
            serializer = TransmissionSerializer(self)
            json_data = serializer.data
            api = ApiDomains()
            url=api.transmission
            #url='https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidatatransmissionAPI'
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
            super().save(*args, **kwargs)
        else:
            print("not connected to backend!")


    def get_absolute_url(self):
        return reverse("transmissions:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-create_date"]



class TransmissionError(models.Model):
    serial = models.CharField(max_length=255, null=True, blank=True)
    transmissionid = models.CharField(max_length=256, null=True, blank=True)
    SenderName = models.CharField(max_length=256, null=True, blank=True)
    errorfield = models.CharField(max_length=256)
    error_description = models.CharField(max_length=256)
    error_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("transmissions:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]


class TransmissionErrorAggregate(models.Model):
    error_date = models.DateTimeField(auto_now=True)
    total = models.CharField(max_length=256)
    clean = models.CharField(max_length=256)
    error = models.CharField(max_length=256)
    source = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return (self.total + " " + self.clean + " " + self.error)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("transmissions:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]

class TransmissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transmission
        fields = '__all__'


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
