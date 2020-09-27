from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.decorators import user_passes_test
import time
from django.db.models import Q
from django.contrib.auth.mixins import(
    LoginRequiredMixin,
    PermissionRequiredMixin
)

from django.urls import reverse
from django.urls import reverse_lazy
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.views import generic
from django.db.models import Count
from employees.models import Employee, EmployeeSerializer, EmployeeErrorSerializer
from employers.models import Employer, EmployerSerializer, EmployerErrorSerializer
from django.contrib.auth.models import User
from bulkuploads.models import BulkUpload
from apicodes.models import APICodes
from employers.models import Employer
from employers.models import EmployerError
from employers.models import EmployerErrorAggregate
from . import models
from . import forms
from employers.forms import EmployerForm
from bulkuploads.forms import BulkUploadForm
import csv
from employers.utils import BulkCreateManager, Notification
from employers.utils import ApiDomains
import os
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid
from django.shortcuts import get_object_or_404
from transmissions.models import Transmission
from mandatories.models import Mandatory
from numchecks.models import Numcheck
from django.utils.encoding import smart_str

import boto3
import requests
import json
import re
from botocore.exceptions import NoCredentialsError
import io
from django.db.models import Count
from datetime import datetime

from events.forms import EventForm
from events.models import Event
from botocore.errorfactory import ClientError
from collections import defaultdict

# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from employers.serializers import EmployerSerializer

from rest_framework import serializers

class SingleEmployer(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'employer_details'
    model = models.Employer
    template_name = 'employers/employer_detail.html'


class ListEmployers(LoginRequiredMixin, generic.ListView):
    model = models.Employer
    template_name = 'employers/employer_list.html'

    def get_queryset(self):
        return models.Employer.objects.all()
        #return models.Employer.objects.prefetch_related('transmission')
        #return models.employer.objects.get(user=request.user)

class CreateEmployer(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'employers.add_employer'
    context_object_name = 'employer_details'
    redirect_field_name = 'employers/employer_list.html'
    form_class = forms.EmployerForm
    model = models.Employer
    template_name = 'employers/employer_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('employers.add_employer'):
            raise HttpResponseForbidden()
        else:
            #form.instance.transmission = self.transmission
            form.instance.creator = self.request.user
            form.instance.record_status = "Created"
            form.instance.source = "Online Transaction"
            if form.instance.transmission == None:
                form.instance.transmissionid = "Unknown"
            else:
                form.instance.transmissionid=form.instance.transmission.transmissionid

            return super().form_valid(form)



#Pull from  backend system of record(SOR)
@permission_required("employers.add_employer")
@login_required
def BackendPull(request, pk):
        # fetch the object related to passed id
        #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataEmployerAPI/latest'

        prod_obj = get_object_or_404(Employer, pk = pk)

        api = ApiDomains()
        url = api.employer + "/" + "latest"
        payload={'ident': prod_obj.employerid}
        resp = requests.get(url, params=payload)
        print(resp.text)
        print(resp.status_code)
        obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
        status_message=obj.http_response_message
        mesg=str(resp.status_code) + " - " + status_message
        if resp.status_code != 200:
            # This means something went wrong.
            #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
            #raise APIError(resp.status_code)
            message={'messages':mesg}
            return render(request, "messages.html", context=message)
        else:
            json_data = json.loads(resp.text)

            # fetch the object related to passed id
            #obj = get_object_or_404(Employer, pk = json_data["LOCAL_ID"])

            # pass the object as instance in form
            #form = EmployerForm(request.POST or None, instance = obj)

            #OVERRIDE THE OBJECT WITH API data
            obj.pk = int(json_data["LOCAL_ID"])
            obj.employerid = json_data["EMPLOYER_ID"]
            obj.name = json_data["NAME"]
            obj.slug = json_data["SLUG"]
            obj.description = json_data["DESCRIPTION"]
            obj.description_html = misaka.html(obj.description)
            obj.FederalEmployerIdentificationNumber = json_data["FEDERAL_EMPLOYER_IDENTIFICATION_NUMBER"]
            obj.CarrierMasterAgreementNumber = json_data["CARRIER_MASTER_AGREEMENT_NUMBER"]

            obj.address_line_1 = json_data["ADDRESS_LINE_1"]
            obj.address_line_2 = json_data["ADDRESS_LINE_2"]
            obj.city = json_data["CITY"]
            obj.state = json_data["STATE"]
            obj.zipcode = json_data["ZIPCODE"]

            obj.purpose = json_data["PURPOSE"]
            obj.planadmin_email = json_data["PLANADMIN_EMAIL"]

            obj.photo = json_data["PHOTO"]
            obj.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj.employer_date = json_data["EMPLOYER_DATE"]

            transmission_id = json_data["TRANSMISSION"]
            transmission_obj = get_object_or_404(Transmission, pk = transmission_id)
            obj.transmission = transmission_obj
            obj.source = json_data["SOURCE"]
            obj.transmissionid = json_data["TRANSMISSIONID"]

            obj.backend_SOR_connection = json_data["CONNECTION"]
            obj.response = json_data["RESPONSE"]
            obj.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj.record_status = json_data["RECORD_STATUS"]

            context = {'employer_details':obj}

            return render(request, "employers/employer_detail.html", context=context)



#Pull from  backend system of record(SOR)
@permission_required("employers.add_employer")
@login_required
def ListEmployersHistory(request, pk):

                context ={}

                prod_obj = get_object_or_404(Employer, pk = pk)

                api = ApiDomains()
                url = api.employer + "/" + "history"
                #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataemployerAPI/history'
                payload={'ident': prod_obj.employerid}

                resp = requests.get(url, params=payload)
                print(resp.status_code)
                obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
                status_message=obj.http_response_message
                mesg=str(resp.status_code) + " - " + status_message

                if resp.status_code != 200:
                    # This means something went wrong.
                    #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
                    #raise APIError(resp.status_code)
                    message={'messages':mesg}
                    return render(request, "messages.html", context=message)
                else:
                    json_data=[]
                    dict_data=[]
                    obj_data=[]
                    json_data = resp.json()
                    #json_data = defaultdict(lambda: -1, json_data)

                    #print(json_data[0])
                    #print(json_data[1])
                    for ix in range(len(json_data)):
                     obj = Employer()
                      #dict_data.append(json.loads(json_data[ix]))
                     obj.pk = int(json_data[ix]["LOCAL_ID"])
                     obj.employerid = json_data[ix]["EMPLOYER_ID"]
                     obj.name = json_data[ix]["NAME"]
                     obj.slug = json_data[ix]["SLUG"]
                     obj.description = json_data[ix]["DESCRIPTION"]
                     obj.description_html = misaka.html(obj.description)
                     obj.FederalEmployerIdentificationNumber = json_data[ix]["FEDERAL_EMPLOYER_IDENTIFICATION_NUMBER"]
                     obj.CarrierMasterAgreementNumber = json_data[ix]["CARRIER_MASTER_AGREEMENT_NUMBER"]

                     obj.address_line_1 = json_data[ix]["ADDRESS_LINE_1"]
                     obj.address_line_2 = json_data[ix]["ADDRESS_LINE_2"]
                     obj.city = json_data[ix]["CITY"]
                     obj.state = json_data[ix]["STATE"]
                     obj.zipcode = json_data[ix]["ZIPCODE"]

                     obj.purpose = json_data[ix]["PURPOSE"]
                     #obj.planadmin_email = json_data[ix]["PLANADMIN_EMAIL"]
                     obj.planadmin_email = json_data[ix].get("PLANADMIN_EMAIL")

                     obj.photo = json_data[ix]["PHOTO"]
                     obj.creator = User.objects.get(pk=int(json_data[ix]["CREATOR"]))
                     #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
                     obj.employer_date = json_data[ix]["EMPLOYER_DATE"]

                     transmission_id = json_data[ix]["TRANSMISSION"]
                     transmission_obj = get_object_or_404(Transmission, pk = transmission_id)
                     obj.transmission = transmission_obj
                     obj.source = json_data[ix]["SOURCE"]
                     #obj.transmissionid = json_data[ix]["TRANSMISSIONID"]
                     obj.transmissionid = json_data[ix].get("TRANSMISSIONID")

                     obj.backend_SOR_connection = json_data[ix]["CONNECTION"]
                     obj.response = json_data[ix]["RESPONSE"]
                     obj.commit_indicator = json_data[ix]["COMMIT_INDICATOR"]
                     obj.record_status = json_data[ix]["RECORD_STATUS"]

                     obj_data.append(obj)

                    context = {'object_list':obj_data}

                    return render(request, "employers/employer_list.html", context=context)

                    #mesg_obj = get_object_or_404(APICodes, http_response_code = 1000)
                    #status_message=mesg_obj.http_response_message
                    #mesg="1000" + " - " + status_message
                    # add form dictionary to context
                    #message={'messages':mesg}
                    #return render(request, "messages.html", context=message)


@permission_required("employers.add_employer")
@login_required
def RefreshEmployer(request, pk):
        # fetch the object related to passed id
        context ={}
        prod_obj = get_object_or_404(Employer, pk = pk)

        api = ApiDomains()
        url = api.employer + "/" + "refresh"
        #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataemployerAPI/history'
        payload={'ident': prod_obj.employerid}

        resp = requests.get(url, params=payload)
        print(resp.status_code)

        obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
        status_message=obj.http_response_message
        mesg=str(resp.status_code) + " - " + status_message

        if resp.status_code != 200:
            # This means something went wrong.
            #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
            #raise APIError(resp.status_code)
            message={'messages':mesg}
            return render(request, "messages.html", context=message)
        else:
            json_data=[]

            json_data = resp.json()
            obj1=Employer()

            #OVERRIDE THE OBJECT WITH API data
            obj1.pk = int(json_data["LOCAL_ID"])
            obj1.employerid = json_data["EMPLOYER_ID"]
            obj1.name = json_data["NAME"]
            obj1.slug = json_data["SLUG"]
            obj1.description = json_data["DESCRIPTION"]
            obj1.description_html = misaka.html(obj1.description)
            obj1.FederalEmployerIdentificationNumber = json_data["FEDERAL_EMPLOYER_IDENTIFICATION_NUMBER"]
            obj1.CarrierMasterAgreementNumber = json_data["CARRIER_MASTER_AGREEMENT_NUMBER"]

            obj1.address_line_1 = json_data["ADDRESS_LINE_1"]
            obj1.address_line_2 = json_data["ADDRESS_LINE_2"]
            obj1.city = json_data["CITY"]
            obj1.state = json_data["STATE"]
            obj1.zipcode = json_data["ZIPCODE"]

            obj1.purpose = json_data["PURPOSE"]

            obj1.photo = json_data["PHOTO"]
            obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj1.employer_date = json_data["EMPLOYER_DATE"]

            transmission_id = json_data["TRANSMISSION"]
            transmission_obj = get_object_or_404(Transmission, pk = transmission_id)
            obj1.transmission = transmission_obj
            obj1.source = json_data["SOURCE"]
            obj1.planadmin_email = json_data["PLANADMIN_EMAIL"]
            obj1.transmissionid = json_data["TRANSMISSIONID"]

            obj1.backend_SOR_connection = json_data["CONNECTION"]
            obj1.response = json_data["RESPONSE"]
            obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj1.record_status = json_data["RECORD_STATUS"]

            #Log events
            event = Event()
            event.EventTypeCode = "ERR"
            event.EventSubjectId = obj1.employerid
            event.EventSubjectName = obj1.name
            event.EventTypeReason = "Employer refreshed from ODS"
            event.source = "Online Transaction"
            event.creator=obj1.creator
            event.save()


            obj1.save()

            context = {'employer_details':obj1}

            return render(request, "employers/employer_detail.html", context=context)


@permission_required("employers.add_employer")
@login_required
def VersionEmployer(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Employer, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = EmployerForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.instance.record_status = "Created"
            form.instance.transmissionid=form.instance.transmission.transmissionid

            #Log events
            event = Event()
            event.EventTypeCode = "ERV"
            event.EventSubjectId = form.instance.employerid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employer versioned"
            event.source = "Online Transaction"
            event.creator=request.user
            event.save()


            form.save()
            return HttpResponseRedirect(reverse("employers:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "employers/employer_form.html", context)


class UpdateEmployer(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'employers.change_employer'
    context_object_name = 'employer_details'
    redirect_field_name = 'employers/employer_detail.html'
    form_class = forms.EmployerForm
    model = models.Employer
    template_name = 'employers/employer_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('employers.change_employer'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            form.instance.record_status = "Updated"
            form.instance.transmissionid=form.instance.transmission.transmissionid

            #Log events
            event = Event()
            event.EventTypeCode = "ERU"
            event.EventSubjectId = form.instance.employerid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employer updated"
            event.source = "Online Transaction"
            event.creator=self.request.user
            event.save()

            return super().form_valid(form)


class DeleteEmployer(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'employers.delete_employer'
    context_object_name = 'employer_details'
    form_class = forms.EmployerForm
    model = models.Employer
    template_name = 'employers/employer_delete_confirm.html'
    success_url = reverse_lazy("employers:all")

    def form_valid(self, form):
        print("hello")
        if not self.request.user.has_perm('employers.delete_employer'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            #Log events
            event = Event()
            event.EventTypeCode = "ERD"
            event.EventSubjectId = form.instance.employerid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employer deleted"
            event.source = "Online Transaction"
            event.creator=self.request.user
            event.save()

            return super().form_valid(form)


@login_required
def SearchEmployersForm(request):
    return render(request,'employers/employer_search_form.html')


class SearchEmployersList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Employer
    template_name = 'employers/employer_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Employer.objects.filter(
            Q(employerid__icontains=query) | Q(name__icontains=query) | Q(description__icontains=query) | Q(purpose__icontains=query) | Q(FederalEmployerIdentificationNumber__icontains=query) | Q(CarrierMasterAgreementNumber__icontains=query) | Q(address_line_1__icontains=query) | Q(city__icontains=query) | Q(state__icontains=query) | Q(zipcode__icontains=query)
        )

        #change start for remote SearchemployersForm
        if not object_list:
            api = ApiDomains()
            url = api.employer + "/" + "refresh"
            #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataemployerAPI/history'
            payload={'ident': query}

            resp = requests.get(url, params=payload)
            print(resp.status_code)

            obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
            status_message=obj.http_response_message
            mesg=str(resp.status_code) + " - " + status_message

            if resp.status_code != 200:
                # This means something went wrong.
                #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
                #raise APIError(resp.status_code)
                #message={'messages':mesg}
                #return render(self.request, "messages.html", context=message)
                print("Status Code: " + str(resp.status_code))
            else:
                json_data=[]

                json_data = resp.json()
                obj_data=[]
                obj1=Employer()

                #OVERRIDE THE OBJECT WITH API data
                obj1.pk = int(json_data["LOCAL_ID"])
                obj1.employerid = json_data["EMPLOYER_ID"]
                obj1.name = json_data["NAME"]
                obj1.slug = json_data["SLUG"]
                obj1.description = json_data["DESCRIPTION"]
                obj1.description_html = misaka.html(obj1.description)
                obj1.FederalEmployerIdentificationNumber = json_data["FEDERAL_EMPLOYER_IDENTIFICATION_NUMBER"]
                obj1.CarrierMasterAgreementNumber = json_data["CARRIER_MASTER_AGREEMENT_NUMBER"]

                obj1.address_line_1 = json_data["ADDRESS_LINE_1"]
                obj1.address_line_2 = json_data["ADDRESS_LINE_2"]
                obj1.city = json_data["CITY"]
                obj1.state = json_data["STATE"]
                obj1.zipcode = json_data["ZIPCODE"]

                obj1.purpose = json_data["PURPOSE"]
                obj1.planadmin_email = json_data["PLANADMIN_EMAIL"]

                obj1.photo = json_data["PHOTO"]
                obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
                #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
                obj1.employer_date = json_data["EMPLOYER_DATE"]

                transmission_id = json_data["TRANSMISSION"]
                transmission_obj = get_object_or_404(Transmission, pk = transmission_id)
                #obj1.transmission = transmission_obj.SenderName
                obj1.transmission = transmission_obj
                obj1.source = json_data["SOURCE"]
                obj1.transmissionid = json_data["TRANSMISSIONID"]

                obj1.backend_SOR_connection = json_data["CONNECTION"]
                obj1.response = json_data["RESPONSE"]
                obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
                obj1.record_status = json_data["RECORD_STATUS"]

                obj1.save()



                #obj_data.append(obj1)
                #print(obj_data)

                #context = {'object_list':obj_data}

                #return render(self.request, "employers/employer_search_list.html", context=context)
                object_remote_list = Employer.objects.filter(employerid=query)
                print(object_remote_list)
                return object_remote_list

        else:
        #change end for remote SearchemployersForm

            return object_list


class ShowEmployeesList(LoginRequiredMixin, generic.ListView):
    model = Employer
    template_name = 'employees/employee_list.html'

    def get_queryset(self): # new
        employer = get_object_or_404(models.Employer, pk=self.kwargs['pk'])
        object_list = employer.employee_set.all()

        return object_list

class ShowAgreementsList(LoginRequiredMixin, generic.ListView):
    model = Employer
    template_name = 'agreements/agreement_list.html'

    def get_queryset(self): # new
        employer = get_object_or_404(models.Employer, pk=self.kwargs['pk'])
        object_list = employer.agreement_set.all()

        return object_list


@permission_required("employers.add_employer")
@login_required
def BulkUploadEmployer(request):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.client('s3')
                    s3.download_file('intellidatastatic1', 'media/employers.csv', 'employers.csv')

                    with open('employers.csv', 'rt') as csv_file:
                        array_good =[]
                        array_bad = []
                        #array_bad =[]
                        next(csv_file) # skip header line

                        execution_start_time = datetime.now()
                        print(execution_start_time)

                        for row in csv.reader(csv_file):
                                                      bad_ind = 0
                                                      name_bad_ind=0
                                                      description_bad_ind=0
                                                      FederalEmployerIdentificationNumber_bad_ind=0
                                                      CarrierMasterAgreementNumber_bad_ind=0
                                                      address_line_1_bad_ind=0
                                                      address_line_2_bad_ind=0
                                                      city_bad_ind=0
                                                      state_bad_ind=0
                                                      zipcode_bad_ind=0
                                                      purpose_bad_ind=0
                                                      planadmin_email_bad_ind=0
                                                      error_description=""
                                                      array1=[]
                                                      array2=[]

                                                      #populate serial number
                                                      serial=row[0]
                                                      array2.append(serial)

                                                    #pass employee:
                                                      employerid=row[1]
                                                      array2.append(employerid)

                                                      transmission=row[12]
                                                      transmission_instance=Transmission.objects.filter(transmissionid=transmission)[0]
                                                      transmission_ident=transmission_instance.pk
                                                      transmission_pk=transmission_ident
                                                      transmissionid=transmission_instance.transmissionid
                                                      sendername=transmission_instance.SenderName
                                                      transmission_planadmin_email=transmission_instance.planadmin_email
                                                      array1=[]
                                                      if transmission == "":
                                                           bad_ind=1
                                                           error_description = "Transmission is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(transmission_pk)
                                                           array1.append(error_description)
                                                           array1.append(transmission_pk)
                                                           array1.append(transmissionid)
                                                           array1.append(sendername)
                                                           array_bad.append(array1)
                                                      else:
                                                           array2.append(transmission_pk)

                                                       #validate name
                                                      name=row[2]
                                                      array1=[]
                                                      if name == "":
                                                          bad_ind = 1
                                                          name_bad_ind=1
                                                          error_description = "Name is mandatory"
                                                          array1.append(serial)
                                                          array1.append(employerid)
                                                          array1.append(name)
                                                          array1.append(name)
                                                          array1.append(error_description)
                                                          array1.append(transmission_pk)
                                                          array1.append(transmissionid)
                                                          array1.append(sendername)
                                                          array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_name').exists()):
                                                         var=Numcheck.objects.filter(attributes='employer_name')[0].numberfield
                                                         if (var == "Yes" and not name.isdigit()):
                                                              array1=[]
                                                              bad_ind = 1
                                                              name_bad_ind = 1
                                                              error_description = "name must be numeric"
                                                              array1.append(serial)
                                                              array1.append(employerid)
                                                              array1.append(name)
                                                              array1.append(name)
                                                              array1.append(error_description)
                                                              array1.append(transmission_pk)
                                                              array1.append(transmissionid)
                                                              array1.append(sendername)
                                                              array_bad.append(array1)

                                                      if name_bad_ind == 0:
                                                          array2.append(name)

                                                      slug=slugify(name)
                                                      #array2.append(slug)

                                                      #validate description
                                                      description=row[3]
                                                      if (Mandatory.objects.filter(attributes='employer_description').exists()):
                                                          var=Mandatory.objects.filter(attributes='employer_description')[0].required
                                                          if (var == "Yes" and description ==""):
                                                               array1=[]
                                                               bad_ind = 1
                                                               description_bad_ind = 1
                                                               error_description = "Description is mandatory"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(description)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)


                                                      if (Numcheck.objects.filter(attributes='employer_description').exists()):
                                                         var=Numcheck.objects.filter(attributes='employer_description')[0].numberfield
                                                         if (var == "Yes" and not description.isdigit()):
                                                              array1=[]
                                                              bad_ind = 1
                                                              description_bad_ind = 1
                                                              error_description = "Description must be numeric"
                                                              array1.append(serial)
                                                              array1.append(employerid)
                                                              array1.append(name)
                                                              array1.append(description)
                                                              array1.append(error_description)
                                                              array1.append(transmission_pk)
                                                              array1.append(transmissionid)
                                                              array1.append(sendername)
                                                              array_bad.append(array1)

                                                      if description_bad_ind == 0:
                                                          array2.append(description)

                                                      description_html = misaka.html(description)

                                                      FederalEmployerIdentificationNumber=row[4]
                                                      if (Mandatory.objects.filter(attributes='employer_FederalEmployerIdentificationNumber').exists()):
                                                          var=Mandatory.objects.filter(attributes='employer_FederalEmployerIdentificationNumber')[0].required
                                                          if (var == "Yes" and FederalEmployerIdentificationNumber ==""):
                                                               array1=[]
                                                               bad_ind = 1
                                                               FederalEmployerIdentificationNumber_bad_ind=1
                                                               error_description = "FederalEmployerIdentificationNumber is mandatory"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(FederalEmployerIdentificationNumber)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_FederalEmployerIdentificationNumber').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_FederalEmployerIdentificationNumber')[0].numberfield
                                                          if (var == "Yes" and not FederalEmployerIdentificationNumber.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               FederalEmployerIdentificationNumber_bad_ind=1
                                                               error_description = "FederalEmployerIdentificationNumber must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(FederalEmployerIdentificationNumber)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if FederalEmployerIdentificationNumber_bad_ind == 0:
                                                          array2.append(FederalEmployerIdentificationNumber)

                                                      CarrierMasterAgreementNumber=row[5]
                                                      if (Mandatory.objects.filter(attributes='employer_CarrierMasterAgreementNumber').exists()):
                                                          var=Mandatory.objects.filter(attributes='employer_CarrierMasterAgreementNumber')[0].required
                                                          if (var == "Yes" and CarrierMasterAgreementNumber ==""):
                                                               array1=[]
                                                               bad_ind = 1
                                                               CarrierMasterAgreementNumber_bad_ind=1
                                                               error_description = "CarrierMasterAgreementNumber is mandatory"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(CarrierMasterAgreementNumber)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_CarrierMasterAgreementNumber').exists()):
                                                          var=Numcheck.objects.filter(attributes='CarrierMasterAgreementNumber')[0].numberfield
                                                          if (var == "Yes" and not CarrierMasterAgreementNumber.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               CarrierMasterAgreementNumber_bad_ind=1
                                                               error_description = "CarrierMasterAgreementNumber must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(CarrierMasterAgreementNumber)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if CarrierMasterAgreementNumber_bad_ind == 0:
                                                          array2.append(CarrierMasterAgreementNumber)

                                                      #validate address
                                                      address_line_1=row[6]
                                                      array1=[]
                                                      if address_line_1 == "":
                                                          bad_ind=1
                                                          address_line_1_bad_ind=1
                                                          error_description = "Address line 1 is mandatory "
                                                          array1.append(serial)
                                                          array1.append(employerid)
                                                          array1.append(name)
                                                          array1.append(address_line_1)
                                                          array1.append(error_description)
                                                          array1.append(transmission_pk)
                                                          array1.append(transmissionid)
                                                          array1.append(sendername)
                                                          array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_address_line_1').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_address_line_1')[0].numberfield
                                                          if (var == "Yes" and not address_line_1.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               address_line_1_bad_ind=1
                                                               error_description = "address_line_1 must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(address_line_1)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if address_line_1_bad_ind == 0:
                                                          array2.append(address_line_1)

                                                      address_line_2=row[7]
                                                      if (Mandatory.objects.filter(attributes='employer_address_line_2').exists()):
                                                          var=Mandatory.objects.filter(attributes='employer_address_line_2')[0].required
                                                          if (var == "Yes" and address_line_2 ==""):
                                                               array1=[]
                                                               bad_ind = 1
                                                               address_line_2_bad_ind=1
                                                               error_description = "address_line_2 is mandatory"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(address_line_2)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_address_line_2').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_address_line_2')[0].numberfield
                                                          if (var == "Yes" and not address_line_2.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               address_line_2_bad_ind=1
                                                               error_description = "address_line_2 must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(address_line_2)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if address_line_2_bad_ind == 0:
                                                          array2.append(address_line_2)

                                                      #validate address line 1
                                                      city=row[8]
                                                      if (Mandatory.objects.filter(attributes='employer_city').exists()):
                                                          var=Mandatory.objects.filter(attributes='employer_city')[0].required
                                                          if (var == "Yes" and city ==""):
                                                               array1=[]
                                                               bad_ind = 1
                                                               city_bad_ind=1
                                                               error_description = "city is mandatory"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(city)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_city').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_city')[0].numberfield
                                                          if (var == "Yes" and not city.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               city_bad_ind=1
                                                               error_description = "city must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(city)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if city_bad_ind == 0:
                                                          array2.append(city)



                                                      state=row[9]
                                                      if (Mandatory.objects.filter(attributes='employer_state').exists()):
                                                           var=Mandatory.objects.filter(attributes='employer_state')[0].required
                                                           if (var == "Yes" and state ==""):
                                                                array1=[]
                                                                bad_ind = 1
                                                                state_bad_ind=1
                                                                error_description = "state is mandatory"
                                                                array1.append(serial)
                                                                array1.append(employerid)
                                                                array1.append(name)
                                                                array1.append(state)
                                                                array1.append(error_description)
                                                                array1.append(transmission_pk)
                                                                array1.append(transmissionid)
                                                                array1.append(sendername)
                                                                array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_state').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_state')[0].numberfield
                                                          if (var == "Yes" and not state.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               state_bad_ind=1
                                                               error_description = "state must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(state)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if state_bad_ind == 0:
                                                          array2.append(state)

                                                           #validate city
                                                      zipcode=row[10]
                                                      if (Mandatory.objects.filter(attributes='employer_zipcode').exists()):
                                                           var=Mandatory.objects.filter(attributes='employer_zipcode')[0].required
                                                           if (var == "Yes" and zipcode ==""):
                                                                array1=[]
                                                                bad_ind = 1
                                                                error_description = "zipcode is mandatory"
                                                                array1.append(serial)
                                                                array1.append(employerid)
                                                                array1.append(name)
                                                                array1.append(zipcode)
                                                                array1.append(error_description)
                                                                array1.append(transmission_pk)
                                                                array1.append(transmissionid)
                                                                array1.append(sendername)
                                                                array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_zipcode').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_zipcode')[0].numberfield
                                                          if (var == "Yes" and not zipcode.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               zipcode_bad_ind=1
                                                               error_description = "zipcode must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(zipcode)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if zipcode_bad_ind == 0:
                                                          array2.append(zipcode)


                                                      purpose=row[11]
                                                      if (Mandatory.objects.filter(attributes='employer_purpose').exists()):
                                                           var=Mandatory.objects.filter(attributes='employer_purpose')[0].required
                                                           if (var == "Yes" and purpose ==""):
                                                                array1=[]
                                                                bad_ind = 1
                                                                purpose_bad_ind=1
                                                                error_description = "purpose is mandatory"
                                                                array1.append(serial)
                                                                array1.append(employerid)
                                                                array1.append(name)
                                                                array1.append(purpose)
                                                                array1.append(error_description)
                                                                array1.append(transmission_pk)
                                                                array1.append(transmissionid)
                                                                array1.append(sendername)
                                                                array_bad.append(array1)

                                                      if (Numcheck.objects.filter(attributes='employer_purpose').exists()):
                                                          var=Numcheck.objects.filter(attributes='employer_purpose')[0].numberfield
                                                          if (var == "Yes" and not purpose.isdigit()):
                                                               array1=[]
                                                               bad_ind = 1
                                                               purpose_bad_ind=1
                                                               error_description = "purpose must be numeric"
                                                               array1.append(serial)
                                                               array1.append(employerid)
                                                               array1.append(name)
                                                               array1.append(purpose)
                                                               array1.append(error_description)
                                                               array1.append(transmission_pk)
                                                               array1.append(transmissionid)
                                                               array1.append(sendername)
                                                               array_bad.append(array1)

                                                      if purpose_bad_ind == 0:
                                                          array2.append(purpose)

                                                      planadmin_email=row[13]
                                                      if (Mandatory.objects.filter(attributes='employer_planadmin_email').exists()):
                                                           var=Mandatory.objects.filter(attributes='employer_planadmin_email')[0].required
                                                           if (var == "Yes" and planadmin_email ==""):
                                                                array1=[]
                                                                bad_ind = 1
                                                                planadmin_email_bad_ind=1
                                                                error_description = "planadmin_email is mandatory"
                                                                array1.append(serial)
                                                                array1.append(employerid)
                                                                array1.append(name)
                                                                array1.append(planadmin_email)
                                                                array1.append(error_description)
                                                                array1.append(transmission_pk)
                                                                array1.append(transmissionid)
                                                                array1.append(sendername)
                                                                array_bad.append(array1)

                                                      if (planadmin_email != "") and (not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", planadmin_email)):
                                                           bad_ind = 1
                                                           planadmin_email_bad_ind = 1
                                                           array1=[]
                                                           error_description = "Invalid email format"
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(planadmin_email)
                                                           array1.append(error_description)
                                                           array1.append(transmission_pk)
                                                           array1.append(transmissionid)
                                                           array1.append(sendername)
                                                           array_bad.append(array1)

                                                      if planadmin_email_bad_ind == 0:
                                                          array2.append(planadmin_email)


                                                      if bad_ind == 0:
                                                          array_good.append(array2)



                        # create good file
                    #with open('employers1.csv', 'w', newline='') as clean_file:
                    ##    writer = csv.writer(clean_file)
                    #    writer.writerows(array_good)

                    buff1 = io.StringIO()

                    writer = csv.writer(buff1, dialect='excel', delimiter=',')
                    writer.writerows(array_good)

                    buff2 = io.BytesIO(buff1.getvalue().encode())

                        # check if a version of the good file already exists
                #    try:
                #        s3.Object('my-bucket', 'dootdoot.jpg').load()
                #    except botocore.exceptions.ClientError as e:
                #        if e.response['Error']['Code'] == "404":
                #            # The object does not exist.
                #            ...
                #        else:
                #            # Something else has gone wrong.
                #            raise
                #    else:
                #        # do something

# create good file
                    try:
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employers1.csv')
                        s3.upload_fileobj(buff2, 'intellidatastatic1', 'media/employers1.csv')
                        print("Good File Upload Successful")

                    except FileNotFoundError:
                         print("The good file was not found")

                    except NoCredentialsError:
                         print("Credentials not available")


                           # create bad file
                    #with open('employer_error.csv', 'w', newline='') as error_file:
                    #       writer = csv.writer(error_file)
                    #       writer.writerows(array1)

                    buff3 = io.StringIO()

                    writer = csv.writer(buff3, dialect='excel', delimiter=',')
                    writer.writerows(array_bad)

                    buff4 = io.BytesIO(buff3.getvalue().encode())


                        # save bad file to S3
                    try:
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employers_error.csv')
                        s3.upload_fileobj(buff4, 'intellidatastatic1', 'media/employers_error.csv')
                        print("Bad File Upload Successful")

                    except FileNotFoundError:
                        print("The bad file was not found")

                    except NoCredentialsError:
                        print("Credentials not available")

                    # load the employer table
                    s3.download_file('intellidatastatic1', 'media/employers1.csv', 'employers1.csv')

                    with open('employers1.csv', 'rt') as csv_file:
                        bulk_mgr = BulkCreateManager(chunk_size=20)

                        for row in csv.reader(csv_file):
                            if row[1] == "":
                                bulk_mgr.add(models.Employer(employerid = str(uuid.uuid4())[26:36],
                                                          name=row[3],
                                                          slug=slugify(row[3]),
                                                          description=row[4],
                                                          description_html = misaka.html(row[4]),
                                                          FederalEmployerIdentificationNumber=row[5],
                                                          CarrierMasterAgreementNumber=row[6],
                                                          address_line_1=row[7],
                                                          address_line_2=row[8],
                                                          city=row[9],
                                                          state=row[10],
                                                          zipcode=row[11],
                                                          purpose=row[12],
                                                          transmission=get_object_or_404(models.Transmission, pk=row[2]),
                                                          transmissionid=models.Transmission.objects.get(pk=row[2]).transmissionid,
                                                          planadmin_email=row[13],
                                                          creator = request.user,
                                                          source="Standard Feed Bulk Upload",
                                                          record_status = "Created",
                                                          bulk_upload_indicator = "Y"
                                                          ))
                            else:
                                bulk_mgr.add(models.Employer(employerid = row[1],
                                                           name=row[3],
                                                           slug=slugify(row[3]),
                                                           description=row[4],
                                                           description_html = misaka.html(row[4]),
                                                           FederalEmployerIdentificationNumber=row[5],
                                                           CarrierMasterAgreementNumber=row[6],
                                                           address_line_1=row[7],
                                                           address_line_2=row[8],
                                                           city=row[9],
                                                           state=row[10],
                                                           zipcode=row[11],
                                                           purpose=row[12],
                                                           transmission=get_object_or_404(models.Transmission, pk=row[2]),
                                                           transmissionid=models.Transmission.objects.get(pk=row[2]).transmissionid,
                                                           planadmin_email=row[13],
                                                           creator = request.user,
                                                           source="Standard Feed Bulk Upload",
                                                           record_status = "Created",
                                                           bulk_upload_indicator = "Y"
                                                          ))

                        bulk_mgr.done()

                        # load the employer error table
                        s3.download_file('intellidatastatic1', 'media/employers_error.csv', 'employers_error.csv')

                        if (os.stat("employers_error.csv").st_size != 0):
                            email_address=transmission_planadmin_email
                            print("email address is " + email_address)
                            if (email_address!="" and email_address!=None):
                                sender_name=sendername
                                attached_file = sender_name + "_employer_feed_error"
                                attachment_file = "employers_error.csv"
                                notification=Notification()
                                notification.EmailPlanAdmin(email_address, attachment_file, attached_file)

                        #Refresh Error table for concerned employer
                        EmployerError.objects.all().delete()

                        with open('employers_error.csv', 'rt') as csv_file:
                            bulk_mgr = BulkCreateManager(chunk_size=20)
                            for row1 in csv.reader(csv_file):
                                bulk_mgr.add(models.EmployerError(serial = row1[0],
                                                          employerid=row1[1],
                                                          name=row1[2],
                                                          errorfield=row1[3],
                                                          error_description=row1[4],
                                                          transmission=get_object_or_404(models.Transmission, pk=row1[5]),
                                                          transmissionid=row1[6],
                                                          sendername=row1[7],
                                                          creator = request.user,
                                                          source="Standard Feed Bulk Upload"
                                                          ))
                            bulk_mgr.done()

                    execution_end_time = datetime.now()
                    duration = (execution_end_time - execution_start_time)
                    print(duration)

                    error_report = EmployerErrorAggregate()

                    error_report.transmission = get_object_or_404(Transmission, pk=transmission_pk)
                    error_report.sendername = sendername

                    error_report.processed_clean=Employer.objects.count()
                    error_report.number_of_error_occurences=EmployerError.objects.count()

                    error_report.total_employers_till_date=(error_report.processed_clean + error_report.number_of_error_occurences)

                    error_report.execution_time_for_this_run=duration

                    with open('employers.csv', 'rt') as csv_file:
                        next(csv_file) # skip header line
                        lines= len(list(csv_file))
                        print(lines)
                        error_report.volume_processed_in_this_run=lines

                    #Refresh Error aggregate table for concerned employer
                    #EmployerErrorAggregate.objects.all().delete()

                    error_report.save()

                    #Log events
                    event = Event()
                    event.EventTypeCode = "ERB"
                    event.EventSubjectId = "bulkemployers"
                    event.EventSubjectName = "Bulk processing"
                    event.EventTypeReason = "Employers uploaded in bulk"
                    event.source = "Standard Feed Bulk Upload"
                    event.creator=request.user
                    event.save()

                    return HttpResponseRedirect(reverse("employers:all"))



                    #return HttpResponseRedirect(reverse("employers:all"))

        else:
                            # add form dictionary to context
                    context["form"] = form

                    return render(request, "bulkuploads/bulkupload_form.html", context)



@permission_required("employers.add_employer")
@login_required
def NonStdBulkUploadEmployer(request):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.resource('s3')

        #add standardization process start
                    #process csv
                    try:
                        #s3.head_object(Bucket='intellidatastatic1', Key='media/employers.csv')
                        obj_to_read1 = s3.Object('intellidatastatic1', 'media/employers-nonstandard-csv.csv')
                        body = obj_to_read1.get()['Body'].read()
                        obj_to_write1 = s3.Object('intellidatastack-s3bucket1-digncfllaejn', 'employers/employers-nonstandard-csv.csv')
                        obj_to_write1.put(Body=body)
                        obj_to_read1.delete()
                    except ClientError:
                        # Not found
                        print("media/employers-nonstandard-csv.csv key does not exist")

                    #process json
                    try:
                        #s3.head_object(Bucket='intellidatastatic1', Key='media/employers-nonstandard-json.rtf')
                        obj_to_read2 = s3.Object('intellidatastatic1', 'media/employers-nonstandard-json')
                        body = obj_to_read2.get()['Body'].read()
                        obj_to_write2 = s3.Object('intellidatastack-s3bucket1-digncfllaejn', 'employers/employers-nonstandard-json')
                        obj_to_write2.put(Body=body)
                        obj_to_read2.delete()
                    except ClientError:
                        # Not found
                        print("media/employers-nonstandard-json key does not exist")

                    #process xml
                    try:
                        #s3.head_object(Bucket='intellidatastatic1', Key='media/employers-nonstandard-json.rtf')
                        obj_to_read2 = s3.Object('intellidatastatic1', 'media/employers-nonstandard-xml')
                        body = obj_to_read2.get()['Body'].read()
                        obj_to_write2 = s3.Object('intellidatastack-s3bucket1-digncfllaejn', 'employers/employers-nonstandard-xml')
                        obj_to_write2.put(Body=body)
                        obj_to_read2.delete()
                    except ClientError:
                        # Not found
                        print("media/employers-nonstandard-xml key does not exist")


                    return HttpResponseRedirect(reverse("employers:all"))
        else:
                           # add form dictionary to context
                   context["form"] = form

                   return render(request, "bulkuploads/bulkupload_form.html", context)


@permission_required("employers.add_employer")
@login_required
def NonStdRefresh(request):
                    #refresh
                    s3 = boto3.client('s3')

                    try:
                        s3.head_object(Bucket='intellidatastatic1', Key='media/employers_nonstd.csv')


                        s3.download_file('intellidatastatic1', 'media/employers_nonstd.csv', 'employers.csv')

                        if os.stat("employers.csv").st_size != 0:

                            with open('employers.csv', 'rt') as csv_file:
                                array_good =[]
                                array_bad = []
                                #array_bad =[]
                                next(csv_file) # skip header line
                                execution_start_time = datetime.now()
                                for row in csv.reader(csv_file):
                                                              bad_ind = 0
                                                              name_bad_ind=0
                                                              description_bad_ind=0
                                                              FederalEmployerIdentificationNumber_bad_ind=0
                                                              CarrierMasterAgreementNumber_bad_ind=0
                                                              address_line_1_bad_ind=0
                                                              address_line_2_bad_ind=0
                                                              city_bad_ind=0
                                                              state_bad_ind=0
                                                              zipcode_bad_ind=0
                                                              purpose_bad_ind=0
                                                              planadmin_email_bad_ind=0
                                                              array1=[]
                                                              array2=[]

                                                              #populate serial number
                                                              serial=row[0]
                                                              array2.append(serial)

                                                            #pass employee:
                                                              employerid=row[1]
                                                              array2.append(employerid)

                                                              transmission=row[12]
                                                              transmissionid=transmission
                                                              transmission_instance=Transmission.objects.filter(transmissionid=transmission)[0]
                                                              transmission_ident=transmission_instance.pk
                                                              transmission_pk=transmission_ident
                                                              sendername=transmission_instance.SenderName
                                                              transmission_planadmin_email=transmission_instance.planadmin_email
                                                              array1=[]
                                                              if transmission == "" or transmission == None:
                                                                   bad_ind=1
                                                                   error_description = "Transmission is mandatory "
                                                                   array1.append(serial)
                                                                   array1.append(employerid)
                                                                   array1.append(name)
                                                                   array1.append(transmission_pk)
                                                                   array1.append(error_description)
                                                                   array1.append(transmission_pk)
                                                                   array1.append(transmissionid)
                                                                   array1.append(sendername)
                                                                   array_bad.append(array1)
                                                              else:
                                                                   array2.append(transmission_pk)

                                                               #validate name
                                                              name=row[2]
                                                              array1=[]
                                                              if name == "":
                                                                  bad_ind = 1
                                                                  name_bad_ind = 1
                                                                  error_description = "Name is mandatory"
                                                                  array1.append(serial)
                                                                  array1.append(employerid)
                                                                  array1.append(name)
                                                                  array1.append(name)
                                                                  array1.append(error_description)
                                                                  array1.append(transmission_pk)
                                                                  array1.append(transmissionid)
                                                                  array1.append(sendername)
                                                                  array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_name').exists()):
                                                                 var=Numcheck.objects.filter(attributes='employer_name')[0].numberfield
                                                                 if (var == "Yes" and not name.isdigit()):
                                                                      array1=[]
                                                                      bad_ind = 1
                                                                      name_bad_ind = 1
                                                                      error_description = "name must be numeric"
                                                                      array1.append(serial)
                                                                      array1.append(employerid)
                                                                      array1.append(name)
                                                                      array1.append(name)
                                                                      array1.append(error_description)
                                                                      array1.append(transmission_pk)
                                                                      array1.append(transmissionid)
                                                                      array1.append(sendername)
                                                                      array_bad.append(array1)

                                                              if name_bad_ind == 0:
                                                                  array2.append(name)

                                                              slug=slugify(name)
                                                              #array2.append(slug)

                                                              description=row[3]
                                                              if (Mandatory.objects.filter(attributes='employer_description').exists()):
                                                                  var=Mandatory.objects.filter(attributes='employer_description')[0].required
                                                                  if (var == "Yes" and description ==""):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       description_bad_ind = 1
                                                                       error_description = "Description is mandatory"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(description)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_description').exists()):
                                                                 var=Numcheck.objects.filter(attributes='employer_description')[0].numberfield
                                                                 if (var == "Yes" and not description.isdigit()):
                                                                      array1=[]
                                                                      bad_ind = 1
                                                                      description_bad_ind = 1
                                                                      error_description = "Description must be numeric"
                                                                      array1.append(serial)
                                                                      array1.append(employerid)
                                                                      array1.append(name)
                                                                      array1.append(description)
                                                                      array1.append(error_description)
                                                                      array1.append(transmission_pk)
                                                                      array1.append(transmissionid)
                                                                      array1.append(sendername)
                                                                      array_bad.append(array1)

                                                              if description_bad_ind == 0:
                                                                  array2.append(description)

                                                              description_html = misaka.html(description)

                                                              FederalEmployerIdentificationNumber=row[4]
                                                              if (Mandatory.objects.filter(attributes='employer_FederalEmployerIdentificationNumber').exists()):
                                                                  var=Mandatory.objects.filter(attributes='employer_FederalEmployerIdentificationNumber')[0].required
                                                                  if (var == "Yes" and FederalEmployerIdentificationNumber ==""):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       FederalEmployerIdentificationNumber_bad_ind=1
                                                                       error_description = "FederalEmployerIdentificationNumber is mandatory"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(FederalEmployerIdentificationNumber)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_FederalEmployerIdentificationNumber').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_FederalEmployerIdentificationNumber')[0].numberfield
                                                                  if (var == "Yes" and not FederalEmployerIdentificationNumber.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       FederalEmployerIdentificationNumber_bad_ind=1
                                                                       error_description = "FederalEmployerIdentificationNumber must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(FederalEmployerIdentificationNumber)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if FederalEmployerIdentificationNumber_bad_ind == 0:
                                                                  array2.append(FederalEmployerIdentificationNumber)


                                                              CarrierMasterAgreementNumber=row[5]
                                                              if (Mandatory.objects.filter(attributes='employer_CarrierMasterAgreementNumber').exists()):
                                                                  var=Mandatory.objects.filter(attributes='employer_CarrierMasterAgreementNumber')[0].required
                                                                  if (var == "Yes" and CarrierMasterAgreementNumber ==""):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       CarrierMasterAgreementNumber_bad_ind=1
                                                                       error_description = "CarrierMasterAgreementNumber is mandatory"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(CarrierMasterAgreementNumber)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_CarrierMasterAgreementNumber').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_CarrierMasterAgreementNumber')[0].numberfield
                                                                  if (var == "Yes" and not CarrierMasterAgreementNumber.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       CarrierMasterAgreementNumber_bad_ind=1
                                                                       error_description = "CarrierMasterAgreementNumber must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(CarrierMasterAgreementNumber)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if CarrierMasterAgreementNumber_bad_ind == 0:
                                                                  array2.append(CarrierMasterAgreementNumber)

                                                              #validate address
                                                              address_line_1=row[6]
                                                              array1=[]
                                                              if address_line_1 == "":
                                                                  bad_ind=1
                                                                  address_line_1_bad_ind=1
                                                                  error_description = "Address line 1 is mandatory "
                                                                  array1.append(serial)
                                                                  array1.append(employerid)
                                                                  array1.append(name)
                                                                  array1.append(address_line_1)
                                                                  array1.append(error_description)
                                                                  array1.append(transmission_pk)
                                                                  array1.append(transmissionid)
                                                                  array1.append(sendername)
                                                                  array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_address_line_1').exists()):
                                                                 var=Numcheck.objects.filter(attributes='employer_address_line_1')[0].numberfield
                                                                 if (var == "Yes" and not address_line_1.isdigit()):
                                                                      array1=[]
                                                                      bad_ind = 1
                                                                      address_line_1_bad_ind=1
                                                                      error_description = "address_line_1 must be numeric"
                                                                      array1.append(serial)
                                                                      array1.append(employerid)
                                                                      array1.append(name)
                                                                      array1.append(address_line_1)
                                                                      array1.append(error_description)
                                                                      array1.append(transmission_pk)
                                                                      array1.append(transmissionid)
                                                                      array1.append(sendername)
                                                                      array_bad.append(array1)

                                                              if address_line_1_bad_ind == 0:
                                                                 array2.append(address_line_1)

                                                              address_line_2=row[7]
                                                              if (Mandatory.objects.filter(attributes='employer_address_line_2').exists()):
                                                                  var=Mandatory.objects.filter(attributes='employer_address_line_2')[0].required
                                                                  if (var == "Yes" and address_line_2 ==""):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       address_line_2_bad_ind=1
                                                                       error_description = "address_line_2 is mandatory"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(address_line_2)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_address_line_2').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_address_line_2')[0].numberfield
                                                                  if (var == "Yes" and not address_line_2.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       address_line_2_bad_ind=1
                                                                       error_description = "address_line_2 must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(address_line_2)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if address_line_2_bad_ind == 0:
                                                                  array2.append(address_line_2)

                                                              #validate address line 1
                                                              city=row[8]
                                                              if (Mandatory.objects.filter(attributes='employer_city').exists()):
                                                                  var=Mandatory.objects.filter(attributes='employer_city')[0].required
                                                                  if (var == "Yes" and city ==""):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       city_bad_ind=1
                                                                       error_description = "city is mandatory"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(city)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_city').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_city')[0].numberfield
                                                                  if (var == "Yes" and not city.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       city_bad_ind=1
                                                                       error_description = "city must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(city)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if city_bad_ind == 0:
                                                                  array2.append(city)


                                                              #validate address line 2
                                                              state=row[9]
                                                              if (Mandatory.objects.filter(attributes='employer_state').exists()):
                                                                   var=Mandatory.objects.filter(attributes='employer_state')[0].required
                                                                   if (var == "Yes" and state ==""):
                                                                        array1=[]
                                                                        bad_ind = 1
                                                                        state_bad_ind=1
                                                                        error_description = "state is mandatory"
                                                                        array1.append(serial)
                                                                        array1.append(employerid)
                                                                        array1.append(name)
                                                                        array1.append(state)
                                                                        array1.append(error_description)
                                                                        array1.append(transmission_pk)
                                                                        array1.append(transmissionid)
                                                                        array1.append(sendername)
                                                                        array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_state').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_state')[0].numberfield
                                                                  if (var == "Yes" and not state.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       state_bad_ind=1
                                                                       error_description = "state must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(state)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if state_bad_ind == 0:
                                                                  array2.append(state)

                                                                   #validate city
                                                              zipcode=row[10]
                                                              array1=[]
                                                              if zipcode == "":
                                                                   bad_ind=1
                                                                   zipcode_bad_ind=1
                                                                   error_description = "Zipcode is mandatory "
                                                                   array1.append(serial)
                                                                   array1.append(employerid)
                                                                   array1.append(name)
                                                                   array1.append(zipcode)
                                                                   array1.append(error_description)
                                                                   array1.append(transmission_pk)
                                                                   array1.append(transmissionid)
                                                                   array1.append(sendername)
                                                                   array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_zipcode').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_zipcode')[0].numberfield
                                                                  if (var == "Yes" and not zipcode.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       zipcode_bad_ind=1
                                                                       error_description = "zipcode must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(zipcode)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if zipcode_bad_ind == 0:
                                                                  array2.append(zipcode)

                                                              purpose=row[11]
                                                              if (Mandatory.objects.filter(attributes='employer_purpose').exists()):
                                                                   var=Mandatory.objects.filter(attributes='employer_purpose')[0].required
                                                                   if (var == "Yes" and purpose ==""):
                                                                        array1=[]
                                                                        bad_ind = 1
                                                                        purpose_bad_ind=1
                                                                        error_description = "purpose is mandatory"
                                                                        array1.append(serial)
                                                                        array1.append(employerid)
                                                                        array1.append(name)
                                                                        array1.append(purpose)
                                                                        array1.append(error_description)
                                                                        array1.append(transmission_pk)
                                                                        array1.append(transmissionid)
                                                                        array1.append(sendername)
                                                                        array_bad.append(array1)

                                                              if (Numcheck.objects.filter(attributes='employer_purpose').exists()):
                                                                  var=Numcheck.objects.filter(attributes='employer_purpose')[0].numberfield
                                                                  if (var == "Yes" and not purpose.isdigit()):
                                                                       array1=[]
                                                                       bad_ind = 1
                                                                       purpose_bad_ind=1
                                                                       error_description = "purpose must be numeric"
                                                                       array1.append(serial)
                                                                       array1.append(employerid)
                                                                       array1.append(name)
                                                                       array1.append(purpose)
                                                                       array1.append(error_description)
                                                                       array1.append(transmission_pk)
                                                                       array1.append(transmissionid)
                                                                       array1.append(sendername)
                                                                       array_bad.append(array1)

                                                              if purpose_bad_ind == 0:
                                                                  array2.append(purpose)

                                                              planadmin_email=row[13]
                                                              if (Mandatory.objects.filter(attributes='employer_planadmin_email').exists()):
                                                                   var=Mandatory.objects.filter(attributes='employer_planadmin_email')[0].required
                                                                   if (var == "Yes" and planadmin_email ==""):
                                                                        array1=[]
                                                                        bad_ind = 1
                                                                        planadmin_email_bad_ind=1
                                                                        error_description = "planadmin_email is mandatory"
                                                                        array1.append(serial)
                                                                        array1.append(employerid)
                                                                        array1.append(name)
                                                                        array1.append(planadmin_email)
                                                                        array1.append(error_description)
                                                                        array1.append(transmission_pk)
                                                                        array1.append(transmissionid)
                                                                        array1.append(sendername)
                                                                        array_bad.append(array1)

                                                              if (planadmin_email != "") and (not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", planadmin_email)):
                                                                   bad_ind = 1
                                                                   planadmin_email_bad_ind = 1
                                                                   array1=[]
                                                                   error_description = "Invalid email format"
                                                                   array1.append(serial)
                                                                   array1.append(employerid)
                                                                   array1.append(name)
                                                                   array1.append(planadmin_email)
                                                                   array1.append(error_description)
                                                                   array1.append(transmission_pk)
                                                                   array1.append(transmissionid)
                                                                   array1.append(sendername)
                                                                   array_bad.append(array1)


                                                              if planadmin_email_bad_ind == 0:
                                                                  array2.append(planadmin_email)

                                                              if bad_ind == 0:
                                                                  array_good.append(array2)



                                # create good file
                            #with open('employers1.csv', 'w', newline='') as clean_file:
                            ##    writer = csv.writer(clean_file)
                            #    writer.writerows(array_good)

                            buff1 = io.StringIO()

                            writer = csv.writer(buff1, dialect='excel', delimiter=',')
                            writer.writerows(array_good)

                            buff2 = io.BytesIO(buff1.getvalue().encode())

                                # check if a version of the good file already exists
                        #    try:
                        #        s3.Object('my-bucket', 'dootdoot.jpg').load()
                        #    except botocore.exceptions.ClientError as e:
                        #        if e.response['Error']['Code'] == "404":
                        #            # The object does not exist.
                        #            ...
                        #        else:
                        #            # Something else has gone wrong.
                        #            raise
                        #    else:
                        #        # do something

        # create good file
                            try:
                                response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employers1.csv')
                                s3.upload_fileobj(buff2, 'intellidatastatic1', 'media/employers1.csv')
                                print("Good File Upload Successful")

                            except FileNotFoundError:
                                 print("The good file was not found")

                            except NoCredentialsError:
                                 print("Credentials not available")


                                   # create bad file
                            #with open('employer_error.csv', 'w', newline='') as error_file:
                            #       writer = csv.writer(error_file)
                            #       writer.writerows(array1)

                            buff3 = io.StringIO()

                            writer = csv.writer(buff3, dialect='excel', delimiter=',')
                            writer.writerows(array_bad)

                            buff4 = io.BytesIO(buff3.getvalue().encode())


                                # save bad file to S3
                            try:
                                response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employers_error.csv')
                                s3.upload_fileobj(buff4, 'intellidatastatic1', 'media/employers_error.csv')
                                print("Bad File Upload Successful")

                            except FileNotFoundError:
                                print("The bad file was not found")

                            except NoCredentialsError:
                                print("Credentials not available")

                            # load the employer table
                            s3.download_file('intellidatastatic1', 'media/employers1.csv', 'employers1.csv')

                            with open('employers1.csv', 'rt') as csv_file:
                                bulk_mgr = BulkCreateManager(chunk_size=20)

                                for row in csv.reader(csv_file):
                                    if row[1] == "":
                                        bulk_mgr.add(models.Employer(employerid = str(uuid.uuid4())[26:36],
                                                                  name=row[3],
                                                                  slug=slugify(row[3]),
                                                                  description=row[4],
                                                                  description_html = misaka.html(row[4]),
                                                                  FederalEmployerIdentificationNumber=row[5],
                                                                  CarrierMasterAgreementNumber=row[6],
                                                                  address_line_1=row[7],
                                                                  address_line_2=row[8],
                                                                  city=row[9],
                                                                  state=row[10],
                                                                  zipcode=row[11],
                                                                  purpose=row[12],
                                                                  transmission=get_object_or_404(models.Transmission, pk=row[2]),
                                                                  transmissionid=models.Transmission.objects.get(pk=row[2]).transmissionid,
                                                                  planadmin_email=row[13],
                                                                  creator = request.user,
                                                                  source="Non-Standard Feed Bulk Upload",
                                                                  record_status = "Created",
                                                                  bulk_upload_indicator = "Y"
                                                                  ))
                                    else:
                                        bulk_mgr.add(models.Employer(employerid = row[1],
                                                                   name=row[3],
                                                                   slug=slugify(row[3]),
                                                                   description=row[4],
                                                                   description_html = misaka.html(row[4]),
                                                                   FederalEmployerIdentificationNumber=row[5],
                                                                   CarrierMasterAgreementNumber=row[6],
                                                                   address_line_1=row[7],
                                                                   address_line_2=row[8],
                                                                   city=row[9],
                                                                   state=row[10],
                                                                   zipcode=row[11],
                                                                   purpose=row[12],
                                                                   transmission=get_object_or_404(models.Transmission, pk=row[2]),
                                                                   transmissionid=models.Transmission.objects.get(pk=row[2]).transmissionid,
                                                                   planadmin_email=row[13],
                                                                   creator = request.user,
                                                                   source="Non-Standard Feed Bulk Upload",
                                                                   record_status = "Created",
                                                                   bulk_upload_indicator = "Y"
                                                                  ))

                                bulk_mgr.done()

                                # load the employer error table
                                s3.download_file('intellidatastatic1', 'media/employers_error.csv', 'employers_error.csv')

                                if (os.stat("employers_error.csv").st_size != 0):
                                    email_address=transmission_planadmin_email
                                    print("email address is " + email_address)
                                    if (email_address!="" and email_address!=None):
                                        sender_name=sendername
                                        attached_file = sender_name + "_employer_feed_error"
                                        attachment_file = "employers_error.csv"
                                        notification=Notification()
                                        notification.EmailPlanAdmin(email_address, attachment_file, attached_file)

                                #Refresh Error table for concerned employer
                                EmployerError.objects.all().delete()

                                with open('employers_error.csv', 'rt') as csv_file:
                                    bulk_mgr = BulkCreateManager(chunk_size=20)
                                    for row1 in csv.reader(csv_file):
                                        bulk_mgr.add(models.EmployerError(serial = row1[0],
                                                                  employerid=row1[1],
                                                                  name=row1[2],
                                                                  errorfield=row1[3],
                                                                  error_description=row1[4],
                                                                  transmission=get_object_or_404(models.Transmission, pk=row1[5]),
                                                                  creator = request.user,
                                                                  source="Non-Standard Feed Bulk Upload"
                                                                  ))
                                    bulk_mgr.done()


                            execution_end_time = datetime.now()
                            duration = (execution_end_time - execution_start_time)

                            error_report = EmployerErrorAggregate()

                            error_report.transmission = get_object_or_404(Transmission, pk=transmission_pk)
                            error_report.processed_clean=Employer.objects.count()
                            error_report.number_of_error_occurences=EmployerError.objects.count()

                            error_report.total_employers_till_date=(error_report.processed_clean + error_report.number_of_error_occurences)

                            error_report.execution_time_for_this_run=duration

                            with open('employers.csv', 'rt') as csv_file:
                                next(csv_file) # skip header line
                                lines= len(list(csv_file))
                                print(lines)
                                error_report.volume_processed_in_this_run=lines

                            #Refresh Error aggregate table for concerned employer
                            #EmployerErrorAggregate.objects.all().delete()

                            error_report.save()

                            #Log events
                            event = Event()
                            event.EventTypeCode = "ERB"
                            event.EventSubjectId = "bulkemployers"
                            event.EventSubjectName = "Bulk processing"
                            event.EventTypeReason = "Employers uploaded in bulk"
                            event.source = "Non-Standard Feed Bulk Upload"
                            event.creator=request.user
                            event.save()

                        #response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employers_nonstd.csv')

                    except ClientError:
                        # Not found
                        print("media/employers_nonstd.csv does not exist")

                    return HttpResponseRedirect(reverse("employers:all"))



@permission_required("employers.add_employer")
@login_required
def BulkUploadSOR(request):

    array = Employer.objects.filter(bulk_upload_indicator='Y')
    serializer = EmployerSerializer(array, many=True)
    json_array = serializer.data

    api = ApiDomains()
    url = api.employer + "/" + "upload"
    #url='https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataemployerAPI'
    #post data to the API for backend connection
    resp = requests.post(url, json=json_array)
    print("status code " + str(resp.status_code))

    if resp.status_code == 502:
        resp.status_code = 201

    obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
    status_message=obj.http_response_message
    mesg=str(resp.status_code) + " - " + status_message

    if resp.status_code != 201:
        # This means something went wrong.
        message={'messages':mesg}
        return render(request, "messages.html", context=message)
    else:
        Employer.objects.filter(bulk_upload_indicator='Y').update(bulk_upload_indicator=" ")

        #Log events
        event = Event()
        event.EventTypeCode = "ERO"
        event.EventSubjectId = "employerod  supload"
        event.EventSubjectName = "Bulk upload to ODS"
        event.EventTypeReason = "Employers uploaded to ODS in bulk"
        event.source = "Online Transaction"
        event.creator=request.user
        event.save()

        return HttpResponseRedirect(reverse("employers:all"))


class ViewEmployerErrorList(LoginRequiredMixin, generic.ListView):
    context_object_name = 'employer_error_list'
    model = models.EmployerError
    template_name = 'employers/employer_error_list.html'

    #form_class = forms.MemberForm

    def get_queryset(self):
    #    return Member.objects.filter(employer=employer_name)
    #    return Member.objects.all
        #return models.Member.objects.prefetch_related('employer')
        #return models.EmployerError.objects.filter(transmission_id=self.kwargs['pk'])
        return models.EmployerError.objects.all()


@api_view(['GET', 'POST'])
def EmployerList(request):

    if request.method == 'GET':
        contacts = Employer.objects.all()
        serializer = EmployerSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = EmployerSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        employer = Employer()
        event = Event()
        s3 = boto3.client('s3')

        bad_ind = 0
        array_bad=[]
        array1=[]

        if serializer.data["employerid"] == '':
            employer.employerid = str(uuid.uuid4())[26:36]
            event.EventTypeReason = "New employer received via API"
        else:
            employer.employerid = serializer.data["employerid"]
            event.EventTypeReason = "Employer added via API"
        #transmission.transmissionid = serializer.data["transmissionid"]
        employer.name = serializer.data["name"]
        if employer.name == "":
            bad_ind = 1
            error_description = "Name is mandatory"
            array1.append(employer.employerid)
            array1.append(employer.name)
            array1.append(employer.name)
            array1.append(error_description)
            array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_name').exists()):
           var=Numcheck.objects.filter(attributes='employer_name')[0].numberfield
           if (var == "Yes" and not employer.name.isdigit()):
                array1=[]
                bad_ind = 1
                name_bad_ind = 1
                error_description = "name must be numeric"
                array1.append(employer.employerid)
                array1.append(employer.name)
                array1.append(employer.name)
                array1.append(error_description)
                array_bad.append(array1)

        employer.slug=slugify(employer.name)

        employer.description = serializer.data["description"]
        if (Mandatory.objects.filter(attributes='employer_description').exists()):
            var=Mandatory.objects.filter(attributes='employer_description')[0].required
            if (var == "Yes" and employer.description ==""):
                 array1=[]
                 bad_ind = 1
                 error_description = "Description is mandatory"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.description)
                 array1.append(error_description)
                 array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_description').exists()):
           var=Numcheck.objects.filter(attributes='employer_description')[0].numberfield
           if (var == "Yes" and employer.description==None):
                array1=[]
                bad_ind = 1
                description_bad_ind = 1
                error_description = "Description must be numeric"
                array1.append(employer.employerid)
                array1.append(employer.name)
                array1.append(employer.description)
                array1.append(error_description)
                array_bad.append(array1)
           elif (var == "Yes" and not employer.description.isdigit()):
               array1=[]
               bad_ind = 1
               description_bad_ind = 1
               error_description = "Description must be numeric"
               array1.append(employer.employerid)
               array1.append(employer.name)
               array1.append(employer.description)
               array1.append(error_description)
               array_bad.append(array1)


        employer.description_html = misaka.html(employer.description)

        employer.FederalEmployerIdentificationNumber = serializer.data["FederalEmployerIdentificationNumber"]
        if (Mandatory.objects.filter(attributes='employer_FederalEmployerIdentificationNumber').exists()):
            var=Mandatory.objects.filter(attributes='employer_FederalEmployerIdentificationNumber')[0].required
            if (var == "Yes" and employer.FederalEmployerIdentificationNumber ==""):
                 array1=[]
                 bad_ind = 1
                 error_description = "FederalEmployerIdentificationNumber is mandatory"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.FederalEmployerIdentificationNumber)
                 array1.append(error_description)
                 array_bad.append(array1)


        if (Numcheck.objects.filter(attributes='employer_FederalEmployerIdentificationNumber').exists()):
            var=Numcheck.objects.filter(attributes='employer_FederalEmployerIdentificationNumber')[0].numberfield
            if (var == "Yes" and employer.FederalEmployerIdentificationNumber == None):
                 array1=[]
                 bad_ind = 1
                 FederalEmployerIdentificationNumber_bad_ind=1
                 error_description = "FederalEmployerIdentificationNumber must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.FederalEmployerIdentificationNumber)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.FederalEmployerIdentificationNumber.isdigit()):
                 array1=[]
                 bad_ind = 1
                 FederalEmployerIdentificationNumber_bad_ind=1
                 error_description = "FederalEmployerIdentificationNumber must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.FederalEmployerIdentificationNumber)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.CarrierMasterAgreementNumber = serializer.data["CarrierMasterAgreementNumber"]
        if (Mandatory.objects.filter(attributes='employer_CarrierMasterAgreementNumber').exists()):
            var=Mandatory.objects.filter(attributes='employer_CarrierMasterAgreementNumber')[0].required
            if (var == "Yes" and employer.CarrierMasterAgreementNumber ==""):
                 array1=[]
                 bad_ind = 1
                 error_description = "CarrierMasterAgreementNumber is mandatory"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.CarrierMasterAgreementNumber)
                 array1.append(error_description)
                 array_bad.append(array1)


        if (Numcheck.objects.filter(attributes='employer_CarrierMasterAgreementNumber').exists()):
            var=Numcheck.objects.filter(attributes='employer_CarrierMasterAgreementNumber')[0].numberfield
            if (var == "Yes" and employer.CarrierMasterAgreementNumber==None):
                 array1=[]
                 bad_ind = 1
                 CarrierMasterAgreementNumber_bad_ind=1
                 error_description = "CarrierMasterAgreementNumber must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.CarrierMasterAgreementNumber)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.CarrierMasterAgreementNumber.isdigit()):
                 array1=[]
                 bad_ind = 1
                 CarrierMasterAgreementNumber_bad_ind=1
                 error_description = "CarrierMasterAgreementNumber must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.CarrierMasterAgreementNumber)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.address_line_1 = serializer.data["address_line_1"]
        array1=[]
        if employer.address_line_1 == "":
            bad_ind=1
            error_description = "Address line 1 is mandatory "
            array1.append(employer.employerid)
            array1.append(employer.name)
            array1.append(employer.address_line_1)
            array1.append(error_description)
            array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_address_line_1').exists()):
            var=Numcheck.objects.filter(attributes='employer_address_line_1')[0].numberfield
            if (var == "Yes" and employer.address_line_1==None):
                 array1=[]
                 bad_ind = 1
                 address_line_1_bad_ind=1
                 error_description = "address_line_1 must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.address_line_1)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.address_line_1.isdigit()):
                 array1=[]
                 bad_ind = 1
                 address_line_1_bad_ind=1
                 error_description = "address_line_1 must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.address_line_1)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.address_line_2 = serializer.data["address_line_2"]
        if (Mandatory.objects.filter(attributes='employer_address_line_2').exists()):
            var=Mandatory.objects.filter(attributes='employer_address_line_2')[0].required
            if (var == "Yes" and employer.address_line_2 ==""):
                 array1=[]
                 bad_ind = 1
                 error_description = "address_line_2 is mandatory"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.address_line_2)
                 array1.append(error_description)
                 array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_address_line_2').exists()):
            var=Numcheck.objects.filter(attributes='employer_address_line_2')[0].numberfield
            if (var == "Yes" and employer.address_line_2==None):
                 array1=[]
                 bad_ind = 1
                 address_line_2_bad_ind=1
                 error_description = "address_line_2 must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.address_line_2)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.address_line_2.isdigit()):
                 array1=[]
                 bad_ind = 1
                 address_line_2_bad_ind=1
                 error_description = "address_line_2 must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.address_line_2)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.city = serializer.data["city"]
        array1=[]
        if employer.city == "":
            bad_ind=1
            error_description = "City is mandatory "
            array1.append(employer.employerid)
            array1.append(employer.name)
            array1.append(employer.city)
            array1.append(error_description)
            array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_city').exists()):
            var=Numcheck.objects.filter(attributes='employer_city')[0].numberfield
            if (var == "Yes" and employer.city==None):
                 array1=[]
                 bad_ind = 1
                 city_bad_ind=1
                 error_description = "city must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.city)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.city.isdigit()):
                 array1=[]
                 bad_ind = 1
                 city_bad_ind=1
                 error_description = "city must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.city)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.state = serializer.data["state"]
        array1=[]
        if employer.state == "":
            bad_ind=1
            error_description = "State is mandatory "
            array1.append(employer.employerid)
            array1.append(employer.name)
            array1.append(employer.state)
            array1.append(error_description)
            array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_state').exists()):
            var=Numcheck.objects.filter(attributes='employer_state')[0].numberfield
            if (var == "Yes" and employer.state==None):
                 array1=[]
                 bad_ind = 1
                 state_bad_ind=1
                 error_description = "state must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.state)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.state.isdigit()):
                 array1=[]
                 bad_ind = 1
                 state_bad_ind=1
                 error_description = "state must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.state)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.zipcode = serializer.data["zipcode"]
        array1=[]
        if employer.zipcode == "":
            bad_ind=1
            error_description = "Zipcode is mandatory "
            array1.append(employer.employerid)
            array1.append(employer.name)
            array1.append(employer.zipcode)
            array1.append(error_description)
            array_bad.append(array1)


        if (Numcheck.objects.filter(attributes='employer_zipcode').exists()):
            var=Numcheck.objects.filter(attributes='employer_zipcode')[0].numberfield
            if (var == "Yes" and employer.zipcode==None):
                 array1=[]
                 bad_ind = 1
                 zipcode_bad_ind=1
                 error_description = "zipcode must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.zipcode)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.zipcode.isdigit()):
                 array1=[]
                 bad_ind = 1
                 zipcode_bad_ind=1
                 error_description = "zipcode must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.zipcode)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.purpose = serializer.data["purpose"]
        if (Mandatory.objects.filter(attributes='employer_purpose').exists()):
            var=Mandatory.objects.filter(attributes='employer_purpose')[0].required
            if (var == "Yes" and employer.purpose ==""):
                 array1=[]
                 bad_ind = 1
                 error_description = "purpose is mandatory"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.purpose)
                 array1.append(error_description)
                 array_bad.append(array1)

        if (Numcheck.objects.filter(attributes='employer_purpose').exists()):
            var=Numcheck.objects.filter(attributes='employer_purpose')[0].numberfield
            if (var == "Yes" and employer.purpose==None):
                 array1=[]
                 bad_ind = 1
                 purpose_bad_ind=1
                 error_description = "purpose must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.purpose)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.purpose.isdigit()):
                 array1=[]
                 bad_ind = 1
                 purpose_bad_ind=1
                 error_description = "purpose must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.purpose)
                 array1.append(error_description)
                 array_bad.append(array1)

        employer.planadmin_email = serializer.data["planadmin_email"]
        if (Mandatory.objects.filter(attributes='employer_planadmin_email').exists()):
            var=Mandatory.objects.filter(attributes='employer_planadmin_email')[0].required
            if (var == "Yes" and employer.planadmin_email ==""):
                 array1=[]
                 bad_ind = 1
                 error_description = "planadmin_email is mandatory"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.planadmin_email)
                 array1.append(error_description)
                 array_bad.append(array1)


        if (Numcheck.objects.filter(attributes='employer_planadmin_email').exists()):
            var=Numcheck.objects.filter(attributes='employer_planadmin_email')[0].numberfield
            if (var == "Yes" and employer.planadmin_email==None):
                 array1=[]
                 bad_ind = 1
                 planadmin_email_bad_ind=1
                 error_description = "planadmin_email must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.planadmin_email)
                 array1.append(error_description)
                 array_bad.append(array1)
            elif (var == "Yes" and not employer.planadmin_email.isdigit()):
                 array1=[]
                 bad_ind = 1
                 planadmin_email_bad_ind=1
                 error_description = "planadmin_email must be numeric"
                 array1.append(employer.employerid)
                 array1.append(employer.name)
                 array1.append(employer.planadmin_email)
                 array1.append(error_description)
                 array_bad.append(array1)

        #get the most recent employer instance and pk
        employer.transmissionid=serializer.data["transmissionid"]
        array1=[]
        if employer.transmissionid == "":
            bad_ind=1
            pk=0
            error_description = "Transmission Code is mandatory "
            array1.append(employer.employerid)
            array1.append(employer.name)
            array1.append(employer.transmissionid)
            array1.append(error_description)
            array_bad.append(array1)
        else:
            transmission_instance=Transmission.objects.filter(transmissionid=employer.transmissionid)[0]
            transmission_ident=transmission_instance.pk
            pk=transmission_ident
            employer.transmission = get_object_or_404(Transmission, pk=pk)

        employer.source = "Post API"

        employer.creator = get_object_or_404(User, pk=serializer.data["creator"])
        #transmission.create_date = serializer.data["create_date"]
        employer.backend_SOR_connection = "Disconnected"
        employer.response = ""
        employer.commit_indicator = "Not Committed"
        employer.record_status = ""
        employer.bulk_upload_indicator="Y"

        if bad_ind==1:
            buff3 = io.StringIO()
            writer = csv.writer(buff3, dialect='excel', delimiter=',')
            writer.writerows(array_bad)
            buff4 = io.BytesIO(buff3.getvalue().encode())

                        # save bad file to S3
            try:
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employers_api_error.csv')
                        s3.upload_fileobj(buff4, 'intellidatastatic1', 'media/employers_api_error.csv')
                        print("Bad File Upload Successful")

            except FileNotFoundError:
                        print("The bad file was not found")

            except NoCredentialsError:
                        print("Credentials not available")

                        # load the employer error table
            s3.download_file('intellidatastatic1', 'media/employers_api_error.csv', 'employers_api_error.csv')

                        #Refresh Error table for concerned employer
            EmployerError.objects.all().delete()

            with open('employers_api_error.csv', 'rt') as csv_file:
                            bulk_mgr = BulkCreateManager(chunk_size=20)
                            for row1 in csv.reader(csv_file):
                                bulk_mgr.add(models.EmployerError(employerid=row1[0],
                                                          name=row1[1],
                                                          errorfield=row1[2],
                                                          error_description=row1[3],
                                                          transmission=get_object_or_404(models.Transmission, pk=pk),
                                                          creator = get_object_or_404(User, pk=serializer.data["creator"]),
                                                          source="Post API"
                                                          ))
                            bulk_mgr.done()

            error_response = EmployerError.objects.all()
            serializer = EmployerErrorSerializer(error_response, many=True)
            return Response(serializer.data)
        else:
            #Log events
            event.EventTypeCode = "ERW"
            event.EventSubjectId = employer.employerid
            event.EventSubjectName = employer.name
            event.source = "Post API"
            event.creator=employer.creator
            event.save()

            employer.save()

            return Response(serializer.data)


    #if serializer.is_valid():
    #    serializer.save()

    #    return Response(serializer.data, status=status.HTTP_201_CREATED)

    #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#rest API call
@api_view(['GET', 'POST'])
def EmployerListByTransmission(request, pk):

    if request.method == 'GET':
        contacts = Employer.objects.filter(transmission_id = pk)
        serializer = EmployerSerializer(contacts, many=True)
        return Response(serializer.data)


    #if serializer.is_valid():
    #    serializer.save()

    #    return Response(serializer.data, status=status.HTTP_201_CREATED)

    #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)


def ExportEmployerDataToCSV(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employers.csv"'

    writer = csv.writer(response)

    writer.writerow(['Serial#', 'Employerid', 'Name', 'Slug', 'Description', 'FederalEmployerIdentificationNumber', 'CarrierMasterAgreementNumber',
                     'Address_line_1', 'Address_line_2', 'City', 'State', 'Zipcode', 'Transmission_Sender_Name', 'Transmission_id', 'Creator', 'Create_date', 'Purpose', 'Planadmin_email', 'Source',
                     'Backend_SOR_connection', 'Commit_indicator', 'Record_status', 'Response', 'Bulk_upload_indicator'])
    #writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])
    queryset=Employer.objects.all().order_by('-employer_date')
    n=0
    for obj in queryset:
        n=n+1
        writer.writerow([
            smart_str(str(n)),
            smart_str(obj.employerid),
            smart_str(obj.name),
            smart_str(obj.slug),
            smart_str(obj.description),
            smart_str(obj.FederalEmployerIdentificationNumber),
            smart_str(obj.CarrierMasterAgreementNumber),
            smart_str(obj.address_line_1),
            smart_str(obj.address_line_2),
            smart_str(obj.city),
            smart_str(obj.state),
            smart_str(obj.zipcode),
            smart_str(obj.transmission),
            smart_str(obj.transmissionid),
            smart_str(obj.creator),
            smart_str(obj.employer_date),
            smart_str(obj.purpose),
            smart_str(obj.planadmin_email),
            smart_str(obj.source),
            smart_str(obj.backend_SOR_connection),
            smart_str(obj.commit_indicator),
            smart_str(obj.record_status),
            smart_str(obj.response),
            smart_str(obj.bulk_upload_indicator)
        ])

    return response
