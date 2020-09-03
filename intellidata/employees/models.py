from django.conf import settings
from datetime import datetime
import uuid
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from employers.models import Employer
from phonenumber_field.modelfields import PhoneNumberField
# from accounts.models import User

import misaka

from employers.utils import ApiDomains
from rest_framework import serializers
import requests
from django.shortcuts import get_object_or_404, render
from apicodes.models import APICodes

from events.forms import EventForm
from events.models import Event

from django.contrib.auth import get_user_model
User = get_user_model()

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_employees check template tag
from django import template
register = template.Library()

class Employee(models.Model):
    employeeid = models.CharField(max_length=255, null=True, blank=True)
    ssn=models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=256)
    slug = models.SlugField(allow_unicode=True)
    gendercode = models.CharField(max_length=255)
    age = models.PositiveIntegerField(default=0)
    birthdate = models.DateField(null=True, blank=True)
    maritalstatus =  models.CharField(max_length=255)


    home_address_line_1 = models.CharField(max_length=256)
    home_address_line_2 = models.CharField(max_length=256, null=True, blank=True)
    home_city = models.CharField(max_length=256)

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

    home_state = models.CharField(max_length=100,
                                      choices=STATE_NAMES,
                                      default=DF)

    home_zipcode = models.CharField(max_length=256)

    mail_address_line_1 = models.CharField(max_length=256, null=True, blank=True)
    mail_address_line_2 = models.CharField(max_length=256, null=True, blank=True)
    mail_city = models.CharField(max_length=256, null=True, blank=True)
    mail_state = models.CharField(max_length=100,
                                      choices=STATE_NAMES,
                                      default=DF)

    mail_zipcode = models.CharField(max_length=256, null=True, blank=True)

    work_address_line_1 = models.CharField(max_length=256, null=True, blank=True)
    work_address_line_2 = models.CharField(max_length=256, null=True, blank=True)
    work_city = models.CharField(max_length=256, null=True, blank=True)
    work_state = models.CharField(max_length=100,
                                      choices=STATE_NAMES,
                                      default=DF)

    work_zipcode = models.CharField(max_length=256, null=True, blank=True)

    email = models.EmailField(max_length=254)
    alternate_email = models.EmailField(max_length=254, blank=True, null=True)


    home_phone = PhoneNumberField(null=True, blank=True, unique=False)
    work_phone = PhoneNumberField(null=True, blank=True, unique=False)
    mobile_phone = PhoneNumberField(null=True, blank=True, unique=False)

    enrollment_method = models.CharField(max_length=255, null=True, blank=True)
    employment_information = models.CharField(max_length=255, null=True, blank=True)

    employer = models.ForeignKey(Employer, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_set")
    employerid = models.CharField(max_length=255, null=True, blank=True)

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    employee_date = models.DateTimeField(auto_now=True)

    #notify = = models.BooleanField()
    sms = models.CharField(max_length=256, null=True, blank=True)
    emailer = models.CharField(max_length=256, null=True, blank=True)

    artefact = models.FileField(blank=True, null=True, default='intellidatastatic.s3.amazonaws.com/media/default.png')
    source = models.CharField(max_length=255, null=True, blank=True)

    backend_SOR_connection = models.CharField(max_length=255, null=True, blank=True, default='Disconnected')
    commit_indicator = models.CharField(max_length=255, null=True, blank=True)
    record_status = models.CharField(max_length=255, null=True, blank=True)
    response = models.CharField(max_length=255, null=True, blank=True)
    bulk_upload_indicator = models.CharField(max_length=1, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if (self.employeeid == None):
            var = str(uuid.uuid4())
            self.employeeid = var[26:36]

            #Log events
            event = Event()
            event.EventTypeCode = "EEA"
            event.EventSubjectId = self.employeeid
            event.EventSubjectName = self.name
            event.EventTypeReason = "Employee added"
            event.source = "Web App"
            event.creator=self.creator
            event.save()

        self.slug = slugify(self.name)
        self.response='Success'

        if (self.bulk_upload_indicator == "Y" and self.backend_SOR_connection != "Disconnected"):
            self.bulk_upload_indicator=""

    #    self.description_html = misaka.html(self.description)
        super().save(*args, **kwargs)

        #connect to backend
        if self.backend_SOR_connection != "Disconnected":
            #converty model object to json
            serializer = EmployeeSerializer(self)
            json_data = serializer.data
            api = ApiDomains()
            url=api.employee
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
            event.EventTypeCode = "EEC"
            event.EventSubjectId = self.employeeid
            event.EventSubjectName = self.name
            event.EventTypeReason = "Employee added to ODS"
            event.source = "Web App"
            event.creator=self.creator
            event.save()

            super().save(*args, **kwargs)
        else:
            print("not connected to backend!")

    def get_absolute_url(self):
        return reverse("employees:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-employee_date"]
        #unique_together = ["name", "group"]

class EmployeeError(models.Model):
    serial = models.CharField(max_length=255, null=True, blank=True)
    employeeid = models.CharField(max_length=256, null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    errorfield = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    employer = models.ForeignKey(Employer, on_delete=models.SET_NULL, null=True, blank=True, related_name="errored_employees")
    error_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=255, null=True, blank=True)
    transmissionid= models.CharField(max_length=255, null=True, blank=True)
    sendername= models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("employees:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]

class EmployeeErrorAggregate(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.SET_NULL, null=True, blank=True)
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
        return reverse("employees:single", kwargs={"pk": self.pk})


    class Meta:
        ordering = ["-error_date"]

# Employee serializer
class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = '__all__'


# Employee Error serializer
class EmployeeErrorSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeError
        fields = '__all__'


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
