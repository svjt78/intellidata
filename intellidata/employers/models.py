from django.conf import settings
from django.shortcuts import get_object_or_404, render
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from apicodes.models import APICodes
from transmissions.models import Transmission

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
#from employers.serializers import EmployerSerializer
import requests
import json

User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_employers check template tag
from django import template
register = template.Library()

class Employer(models.Model):
    employerid = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True)
    description = models.TextField(blank=True, default='')
    description_html = models.TextField(editable=False, default='', blank=True)
    FederalEmployerIdentificationNumber=models.CharField(max_length=255, null=True, blank=True)
    CarrierMasterAgreementNumber=models.CharField(max_length=255, null=True, blank=True)

    address_line_1 = models.CharField(max_length=256)
    address_line_2 = models.CharField(max_length=256, null=True, blank=True)
    city = models.CharField(max_length=256)

    DF = 'Choose state'
    AL = 'AL'
    AK = 'AK'
    AZ = 'AZ'
    AR = 'AR'
    CA = 'CA'
    CO = 'CO'
    CT = 'CT'
    DE = 'DE'
    FL = 'FL'
    GA = 'GA'
    HI = 'HI'
    ID = 'ID'
    IL = 'IL'
    IN = 'IN'
    IA = 'IA'
    KS = 'KS'
    KY = 'KY'
    LA = 'LA'
    ME = 'ME'
    MD = 'MD'
    MA = 'MA'
    MI = 'MI'
    MN = 'MN'
    MS = 'MS'
    MO = 'MO'
    MT = 'MT'
    NE = 'NE'
    NV = 'NV'
    NH = 'NH'
    NJ = 'NJ'
    NM = 'NM'
    NY = 'NY'
    NC = 'NC'
    ND = 'ND'
    OH = 'OH'
    OK = 'OK'
    OR = 'OR'
    PA = 'PA'
    RI = 'RI'
    SC = 'SC'
    SD = 'SD'
    TN = 'TN'
    TX = 'TX'
    UT = 'UT'
    VT = 'VT'
    VA = 'VA'
    WA = 'WA'
    WV = 'WV'
    WI = 'WI'
    WY = 'WY'

    STATE_NAMES = (
        (DF, 'Choose state'),
        (AL, 'Alabama'),
        (AK, 'Alaska'),
        (AZ, 'Arizona'),
        (AR, 'Arkansas'),
        (CA, 'California'),
        (CO, 'Colorado'),
        (CT, 'Connecticut'),
        (DE, 'Delaware'),
        (FL, 'Florida'),
        (GA, 'Georgia'),
        (HI, 'Hawaii'),
        (ID, 'Idaho'),
        (IL, 'Illinois'),
        (IN, 'Indiana'),
        (IA, 'Iowa'),
        (KS, 'Kansas'),
        (KY, 'Kentucky'),
        (LA, 'Louisiana'),
        (ME, 'Maine'),
        (MD, 'Maryland'),
        (MA, 'Massachusetts'),
        (MI, 'Michigan'),
        (MN, 'Minnesota'),
        (MS, 'Mississippi'),
        (MO, 'Missouri'),
        (MT, 'Montana'),
        (NE, 'Nebraska'),
        (NV, 'Nevada'),
        (NH, 'New Hampshire'),
        (NJ, 'New Jersey'),
        (NM, 'New Mexico'),
        (NY, 'New York'),
        (NC, 'North Carolina'),
        (ND, 'North Dakota'),
        (OH, 'Ohio'),
        (OK, 'Oklahoma'),
        (OR, 'Oregon'),
        (PA, 'Pennsylvania'),
        (RI, 'Rhode Island'),
        (SC, 'South Carolina'),
        (SD, 'South Dakota'),
        (TN, 'Tennessee'),
        (TX, 'Texas'),
        (UT, 'Utah'),
        (VT, 'Vermont'),
        (VA, 'Virginia'),
        (WA, 'Washington'),
        (WV, 'West Virginia'),
        (WI, 'Wisconsin'),
        (WY, 'Wyoming'),

    )

    state = models.CharField(max_length=100,
                                      choices=STATE_NAMES,
                                      default=DF)

    zipcode = models.CharField(max_length=256)

    transmission = models.ForeignKey(Transmission, on_delete=models.SET_NULL, null=True, blank=True, related_name="employer_set")

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    employer_date = models.DateTimeField(auto_now=True)
    photo = models.ImageField(blank=True, null=True)
    purpose = models.CharField(max_length=255, null=True, default='', blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)

    backend_SOR_connection = models.CharField(max_length=255, default='Disconnected')
    commit_indicator = models.CharField(max_length=255, default='Not Committed')
    record_status = models.CharField(max_length=255, null=True, blank=True)
    response = models.CharField(max_length=255, null=True, blank=True)
    bulk_upload_indicator = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if (self.employerid == None):
            var = str(uuid.uuid4())
            self.employerid = var[26:36]

            #Log events
            event = Event()
            event.EventTypeCode = "ERA"
            event.EventSubjectId = self.employerid
            event.EventSubjectName = self.name
            event.EventTypeReason = "Employer added"
            event.source = "Web App"
            event.creator=self.creator
            event.save()

        self.slug = slugify(self.name)
        self.description_html = misaka.html(self.description)
        self.response='Success'
        super().save(*args, **kwargs)

        #connect to backend
        if self.backend_SOR_connection != "Disconnected":
            #converty model object to json
            serializer = EmployerSerializer(self)
            json_data = serializer.data
            api = ApiDomains()
            url=api.employer
            #url='https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataemployerAPI'
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
            event.EventTypeCode = "ERC"
            event.EventSubjectId = self.employerid
            event.EventSubjectName = self.name
            event.EventTypeReason = "Employer added to ODS"
            event.source = "Web App"
            event.creator=self.creator
            event.save()

            super().save(*args, **kwargs)
        else:
            print("not connected to backend!")


    def get_absolute_url(self):
        return reverse("employers:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-employer_date"]
        #unique_together = ("name", "type", "employer_date")


class EmployerError(models.Model):
    serial = models.CharField(max_length=255, null=True, blank=True)
    employerid = models.CharField(max_length=256, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    errorfield = models.CharField(max_length=256)
    error_description = models.CharField(max_length=256)
    transmission = models.ForeignKey(Transmission, on_delete=models.SET_NULL, null=True, blank=True, related_name="errored_employers")
    error_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("employers:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]

class EmployerErrorAggregate(models.Model):
    transmission = models.ForeignKey(Transmission, on_delete=models.SET_NULL, null=True, blank=True)
    error_date = models.DateTimeField(auto_now=True)
    total = models.CharField(max_length=256)
    clean = models.CharField(max_length=256)
    error = models.CharField(max_length=256)
    source = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return (self.total + " " + self.clean + " " + self.error)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("employers:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]


class EmployerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employer
        fields = '__all__'


class EmployerErrorSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployerError
        fields = '__all__'


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
