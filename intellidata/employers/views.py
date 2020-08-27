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
from employers.models import Employer
from employees.models import Employee, EmployeeSerializer
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
from employers.utils import BulkCreateManager
from employers.utils import ApiDomains
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid
from django.shortcuts import get_object_or_404
from transmissions.models import Transmission

import boto3
import requests
import json
import re
from botocore.exceptions import NoCredentialsError
import io
from django.db.models import Count

from events.forms import EventForm
from events.models import Event

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
            form.instance.source = "Web App"

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

            obj.photo = json_data["PHOTO"]
            obj.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj.employer_date = json_data["EMPLOYER_DATE"]

            transmission_id = json_data["TRANSMISSION"]
            transmission_obj = get_object_or_404(Transmission, pk = transmission_id)
            obj.transmission = transmission_obj

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

                     obj.photo = json_data[ix]["PHOTO"]
                     obj.creator = User.objects.get(pk=int(json_data[ix]["CREATOR"]))
                     #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
                     obj.employer_date = json_data[ix]["EMPLOYER_DATE"]

                     transmission_id = json_data[ix]["TRANSMISSION"]
                     transmission_obj = get_object_or_404(Transmission, pk = transmission_id)
                     obj.transmission = transmission_obj

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
            event.source = "Web App"
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

            #Log events
            event = Event()
            event.EventTypeCode = "ERV"
            event.EventSubjectId = form.instance.employerid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employer versioned"
            event.source = "Web App"
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

            #Log events
            event = Event()
            event.EventTypeCode = "ERU"
            event.EventSubjectId = form.instance.employerid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employer updated"
            event.source = "Web App"
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
            event.source = "Web App"
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
                obj1.description_html = misaka.html(obj.description)
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
                #obj1.transmission = transmission_obj.SenderName
                obj1.transmission = transmission_obj

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
                        for row in csv.reader(csv_file):
                                                      bad_ind = 0
                                                      array1=[]
                                                      array2=[]

                                                      #populate serial number
                                                      serial=row[0]
                                                      array2.append(serial)

                                                    #pass employee:
                                                      employerid=row[1]
                                                      array2.append(employerid)
                                                       #validate name
                                                      name=row[2]
                                                      if name == "":
                                                          bad_ind = 1
                                                          error_description = "Name is mandatory"
                                                          array1.append(serial)
                                                          array1.append(employerid)
                                                          array1.append(name)
                                                          array1.append(name)
                                                          array1.append(error_description)
                                                          array_bad.append(array1)

                                                      else:
                                                          array2.append(name)

                                                      slug=slugify(name)
                                                      #array2.append(slug)

                                                      description=row[3]
                                                      array2.append(description)

                                                      description_html = misaka.html(description)

                                                      FederalEmployerIdentificationNumber=row[4]
                                                      array2.append(FederalEmployerIdentificationNumber)

                                                      CarrierMasterAgreementNumber=row[5]
                                                      array2.append(CarrierMasterAgreementNumber)

                                                      #validate address
                                                      address_line_1=row[6]
                                                      array1=[]
                                                      if address_line_1 == "":
                                                          bad_ind=1
                                                          error_description = "Address line 1 is mandatory "
                                                          array1.append(serial)
                                                          array1.append(employerid)
                                                          array1.append(name)
                                                          array1.append(address_line_1)
                                                          array1.append(error_description)
                                                          array_bad.append(array1)
                                                      else:
                                                           array2.append(address_line_1)

                                                      address_line_2=row[7]
                                                      array2.append(address_line_2)

                                                      #validate address line 1
                                                      city=row[8]
                                                      array1=[]
                                                      if city == "":
                                                           bad_ind=1
                                                           error_description = "City is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(city)
                                                           array1.append(error_description)
                                                           array_bad.append(array1)
                                                      else:
                                                          array2.append(city)


                                                      #validate address line 2
                                                      state=row[9]
                                                      array2.append(state)

                                                           #validate city
                                                      zipcode=row[10]
                                                      array1=[]
                                                      if zipcode == "":
                                                           bad_ind=1
                                                           error_description = "Zipcode is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(zipcode)
                                                           array1.append(error_description)
                                                           array_bad.append(array1)
                                                      else:
                                                           array2.append(zipcode)

                                                      purpose=row[11]
                                                      array2.append(purpose)


                                                      transmission_pk=row[12]
                                                      array1=[]
                                                      if transmission_pk == "":
                                                           bad_ind=1
                                                           error_description = "Transmission Code is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(transmission_pk)
                                                           array1.append(error_description)
                                                           array_bad.append(array1)
                                                      else:
                                                           array2.append(transmission_pk)

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
                                                          name=row[2],
                                                          slug=slugify(row[2]),
                                                          description=row[3],
                                                          description_html = misaka.html(row[3]),
                                                          FederalEmployerIdentificationNumber=row[4],
                                                          CarrierMasterAgreementNumber=row[5],
                                                          address_line_1=row[6],
                                                          address_line_2=row[7],
                                                          city=row[8],
                                                          state=row[9],
                                                          zipcode=row[10],
                                                          purpose=row[11],
                                                          transmission=get_object_or_404(models.Transmission, pk=transmission_pk),
                                                          creator = request.user,
                                                          source="Web App Bulk Upload",
                                                          record_status = "Created",
                                                          bulk_upload_indicator = "Y"
                                                          ))
                            else:
                                bulk_mgr.add(models.Employer(employerid = row[1],
                                                           name=row[2],
                                                           slug=slugify(row[2]),
                                                           description=row[3],
                                                           description_html = misaka.html(row[3]),
                                                           FederalEmployerIdentificationNumber=row[4],
                                                           CarrierMasterAgreementNumber=row[5],
                                                           address_line_1=row[6],
                                                           address_line_2=row[7],
                                                           city=row[8],
                                                           state=row[9],
                                                           zipcode=row[10],
                                                           purpose=row[11],
                                                           transmission=get_object_or_404(models.Transmission, pk=transmission_pk),
                                                           creator = request.user,
                                                           source="Web App Bulk Upload",
                                                           record_status = "Created",
                                                           bulk_upload_indicator = "Y"
                                                          ))

                        bulk_mgr.done()

                        # load the employer error table
                        s3.download_file('intellidatastatic1', 'media/employers_error.csv', 'employers_error.csv')

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
                                                          transmission=get_object_or_404(models.Transmission, pk=transmission_pk),
                                                          creator = request.user,
                                                          source="Web App Bulk Upload"
                                                          ))
                            bulk_mgr.done()


                    error_report = EmployerErrorAggregate()

                    error_report.transmission = get_object_or_404(Transmission, pk=transmission_pk)
                    error_report.clean=Employer.objects.count()
                    error_report.error=EmployerError.objects.count()

                    error_report.total=(error_report.clean + error_report.error)

                    #Refresh Error aggregate table for concerned employer
                    EmployerErrorAggregate.objects.all().delete()

                    error_report.save()

                    #Log events
                    event = Event()
                    event.EventTypeCode = "ERB"
                    event.EventSubjectId = "bulkemployers"
                    event.EventSubjectName = "Bulk processing"
                    event.EventTypeReason = "Employers uploaded in bulk"
                    event.source = "Web App"
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



        #add standardization process start

                    s3 = boto3.resource('s3')
                    obj_to_read = s3.Object('intellidatastatic1', 'media/employers.csv')
                    body = obj_to_read.get()['Body'].read()

                    obj_to_write = s3.Object('intellidatastack-s3bucket1-digncfllaejn', 'employers/employers.csv')
                    obj_to_write.put(Body=body)


@permission_required("employers.add_employer")
@login_required
def NonStdRefresh(request):
                    #refresh
                    s3.download_file('intellidatastatic1', 'media/employers_nonstd.csv', 'employers.csv')

                    with open('employers.csv', 'rt') as csv_file:
                        array_good =[]
                        array_bad = []
                        #array_bad =[]
                        next(csv_file) # skip header line
                        for row in csv.reader(csv_file):
                                                      bad_ind = 0
                                                      array1=[]
                                                      array2=[]

                                                      #populate serial number
                                                      serial=row[0]
                                                      array2.append(serial)

                                                    #pass employee:
                                                      employerid=row[1]
                                                      array2.append(employerid)
                                                       #validate name
                                                      name=row[2]
                                                      if name == "":
                                                          bad_ind = 1
                                                          error_description = "Name is mandatory"
                                                          array1.append(serial)
                                                          array1.append(employerid)
                                                          array1.append(name)
                                                          array1.append(name)
                                                          array1.append(error_description)
                                                          array_bad.append(array1)

                                                      else:
                                                          array2.append(name)

                                                      slug=slugify(name)
                                                      #array2.append(slug)

                                                      description=row[3]
                                                      array2.append(description)

                                                      description_html = misaka.html(description)

                                                      FederalEmployerIdentificationNumber=row[4]
                                                      array2.append(FederalEmployerIdentificationNumber)

                                                      CarrierMasterAgreementNumber=row[5]
                                                      array2.append(CarrierMasterAgreementNumber)

                                                      #validate address
                                                      address_line_1=row[6]
                                                      array1=[]
                                                      if address_line_1 == "":
                                                          bad_ind=1
                                                          error_description = "Address line 1 is mandatory "
                                                          array1.append(serial)
                                                          array1.append(employerid)
                                                          array1.append(name)
                                                          array1.append(address_line_1)
                                                          array1.append(error_description)
                                                          array_bad.append(array1)
                                                      else:
                                                           array2.append(address_line_1)

                                                      address_line_2=row[7]
                                                      array2.append(address_line_2)

                                                      #validate address line 1
                                                      city=row[8]
                                                      array1=[]
                                                      if city == "":
                                                           bad_ind=1
                                                           error_description = "City is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(city)
                                                           array1.append(error_description)
                                                           array_bad.append(array1)
                                                      else:
                                                          array2.append(city)


                                                      #validate address line 2
                                                      state=row[9]
                                                      array2.append(state)

                                                           #validate city
                                                      zipcode=row[10]
                                                      array1=[]
                                                      if zipcode == "":
                                                           bad_ind=1
                                                           error_description = "Zipcode is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(zipcode)
                                                           array1.append(error_description)
                                                           array_bad.append(array1)
                                                      else:
                                                           array2.append(zipcode)

                                                      purpose=row[11]
                                                      array2.append(purpose)


                                                      transmission_pk=row[12]
                                                      array1=[]
                                                      if transmission_pk == "":
                                                           bad_ind=1
                                                           error_description = "Transmission Code is mandatory "
                                                           array1.append(serial)
                                                           array1.append(employerid)
                                                           array1.append(name)
                                                           array1.append(transmission_pk)
                                                           array1.append(error_description)
                                                           array_bad.append(array1)
                                                      else:
                                                           array2.append(transmission_pk)

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
                                                          name=row[2],
                                                          slug=slugify(row[2]),
                                                          description=row[3],
                                                          description_html = misaka.html(row[3]),
                                                          FederalEmployerIdentificationNumber=row[4],
                                                          CarrierMasterAgreementNumber=row[5],
                                                          address_line_1=row[6],
                                                          address_line_2=row[7],
                                                          city=row[8],
                                                          state=row[9],
                                                          zipcode=row[10],
                                                          purpose=row[11],
                                                          transmission=get_object_or_404(models.Transmission, pk=transmission_pk),
                                                          creator = request.user,
                                                          source="Web App Bulk Upload",
                                                          record_status = "Created",
                                                          bulk_upload_indicator = "Y"
                                                          ))
                            else:
                                bulk_mgr.add(models.Employer(employerid = row[1],
                                                           name=row[2],
                                                           slug=slugify(row[2]),
                                                           description=row[3],
                                                           description_html = misaka.html(row[3]),
                                                           FederalEmployerIdentificationNumber=row[4],
                                                           CarrierMasterAgreementNumber=row[5],
                                                           address_line_1=row[6],
                                                           address_line_2=row[7],
                                                           city=row[8],
                                                           state=row[9],
                                                           zipcode=row[10],
                                                           purpose=row[11],
                                                           transmission=get_object_or_404(models.Transmission, pk=transmission_pk),
                                                           creator = request.user,
                                                           source="Web App Bulk Upload",
                                                           record_status = "Created",
                                                           bulk_upload_indicator = "Y"
                                                          ))

                        bulk_mgr.done()

                        # load the employer error table
                        s3.download_file('intellidatastatic1', 'media/employers_error.csv', 'employers_error.csv')

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
                                                          transmission=get_object_or_404(models.Transmission, pk=transmission_pk),
                                                          creator = request.user,
                                                          source="Web App Bulk Upload"
                                                          ))
                            bulk_mgr.done()


                    error_report = EmployerErrorAggregate()

                    error_report.transmission = get_object_or_404(Transmission, pk=transmission_pk)
                    error_report.clean=Employer.objects.count()
                    error_report.error=EmployerError.objects.count()

                    error_report.total=(error_report.clean + error_report.error)

                    #Refresh Error aggregate table for concerned employer
                    EmployerErrorAggregate.objects.all().delete()

                    error_report.save()

                    #Log events
                    event = Event()
                    event.EventTypeCode = "ERB"
                    event.EventSubjectId = "bulkemployers"
                    event.EventSubjectName = "Bulk processing"
                    event.EventTypeReason = "Employers uploaded in bulk"
                    event.source = "Web App"
                    event.creator=request.user
                    event.save()


                    return HttpResponseRedirect(reverse("employers:all"))


@permission_required("employers.add_employer")
@login_required
def BulkUploadEmployer_deprecated(request):

    context ={}

    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
                form.instance.creator = request.user
                form.save()

                #s3_resource = boto3.resource('s3')
                #s3_resource.Object("intellidatastatic1", "media/employers.csv").download_file(f'/tmp/{"employers.csv"}') # Python 3.6+
                s3 = boto3.client('s3')
                s3.download_file('intellidatastatic1', 'media/employers.csv', 'employers.csv')

                #with open('/tmp/{"employers.csv"}', 'rt') as csv_file:
                with open('employers.csv', 'rt') as csv_file:
                    bulk_mgr = BulkCreateManager(chunk_size=20)
                    for row in csv.reader(csv_file):
                        bulk_mgr.add(models.Employer(

                                                  employerid = str(uuid.uuid4())[26:36],
                                                  name=row[0],
                                                  slug=slugify(row[0]),
                                                  type=row[1],
                                                  description=row[2],
                                                  description_html = misaka.html(row[2]),
                                                  coverage_limit=row[3],
                                                  price_per_1000_units=row[4],
                                                  creator = request.user,
                                                  record_status = "Created",
                                                  bulk_upload_indicator = "Y"
                                                  ))
                    bulk_mgr.done()

                return HttpResponseRedirect(reverse("employers:all"))
    else:
            # add form dictionary to context
            context["form"] = form

            return render(request, "bulkuploads/bulkupload_form.html", context)


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
        event.source = "Web App"
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

        if serializer.data["employerid"] == '':
            employer.employerid = str(uuid.uuid4())[26:36]
            event.EventTypeReason = "New employer received via API"
        else:
            employer.employerid = serializer.data["employerid"]
            event.EventTypeReason = "Employer added via API"
        #transmission.transmissionid = serializer.data["transmissionid"]
        employer.name = serializer.data["name"]
        employer.slug=slugify(employer.name),

        employer.description = serializer.data["description"]
        employer.description_html = misaka.html(employer.description),
        employer.FederalEmployerIdentificationNumber = serializer.data["FederalEmployerIdentificationNumber"]
        employer.CarrierMasterAgreementNumber = serializer.data["CarrierMasterAgreementNumber"]
        employer.address_line_1 = serializer.data["address_line_1"]
        employer.address_line_2 = serializer.data["address_line_2"]
        employer.city = serializer.data["city"]
        employer.state = serializer.data["state"]
        employer.zipcode = serializer.data["zipcode"]
        employer.purpose = serializer.data["purpose"]
        employer.transmission = get_object_or_404(Transmission, pk=serializer.data["transmission"])

        employer.source = "API Call"

        employer.creator = get_object_or_404(User, pk=serializer.data["creator"])
        #transmission.create_date = serializer.data["create_date"]
        employer.backend_SOR_connection = "Disconnected"
        employer.response = ""
        employer.commit_indicator = "Not Committed"
        employer.record_status = ""

        #Log events
        event.EventTypeCode = "ERW"
        event.EventSubjectId = employer.employerid
        event.EventSubjectName = employer.name
        event.source = "API Call"
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
    elif request.method == 'POST':
        serializer = EmployerSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        employer = Employer()
        event = Event()

        if serializer.data["employerid"] == '':
            employer.employerid = str(uuid.uuid4())[26:36]
            event.EventTypeReason = "New employer received via API"
        else:
            employer.employerid = serializer.data["employerid"]
            event.EventTypeReason = "Employer received via API"
        #transmission.transmissionid = serializer.data["transmissionid"]
        employer.name = serializer.data["name"]
        employer.slug=slugify(employer.name)

        employer.description = serializer.data["description"]
        employer.description_html = misaka.html(employer.description)
        employer.FederalEmployerIdentificationNumber = serializer.data["FederalEmployerIdentificationNumber"]
        employer.CarrierMasterAgreementNumber = serializer.data["CarrierMasterAgreementNumber"]
        employer.address_line_1 = serializer.data["address_line_1"]
        employer.address_line_2 = serializer.data["address_line_2"]
        employer.city = serializer.data["city"]
        employer.state = serializer.data["state"]
        employer.zipcode = serializer.data["zipcode"]
        employer.purpose = serializer.data["purpose"]
        employer.transmission = get_object_or_404(Transmission, pk=serializer.data["transmission"])

        employer.source = "API Call"

        employer.crerator = get_object_or_404(User, pk=serializer.data["creator"])
        #transmission.create_date = serializer.data["create_date"]
        employer.backend_SOR_connection = "Disconnected"
        employer.response = ""
        employer.commit_indicator = "Not Committed"
        employer.record_status = ""

        #Log events
        event.EventTypeCode = "ERW"
        event.EventSubjectId = employer.employerid
        event.EventSubjectName = employer.name
        event.source = "API Call"
        event.creator=employer.creator
        event.save()

        employer.save()
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
