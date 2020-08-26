from django.contrib import messages
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required
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
from employers.models import Employer
from employees.models import Employee
from employees.models import EmployeeError
from employees.models import EmployeeErrorAggregate
from . import models
from . import forms
from employees.forms import EmployeeForm
from bulkuploads.models import BulkUpload
from bulkuploads.forms import BulkUploadForm
import boto3
from botocore.exceptions import ClientError
import json
import csv
from employers.utils import BulkCreateManager
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid
from employers.utils import ApiDomains
from apicodes.models import APICodes
from employers.utils import Notification
import requests
from django.contrib.auth.models import User
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
from employees.serializers import EmployeeSerializer


class SingleEmployee(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'employee_details'
    model = models.Employee
    template_name = 'employees/employee_detail.html'
    #form_class = forms.employeeForm

class ListEmployees(LoginRequiredMixin, generic.ListView):
    context_object_name = 'employee_list'
    model = models.Employee
    template_name = 'employees/employee_list.html'

    #form_class = forms.employeeForm

    def get_queryset(self):
    #    return employee.objects.filter(employer=employer_name)
    #    return employee.objects.all
        return models.Employee.objects.prefetch_related('employer')


class CreateEmployee(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    #fields = ("name", "age")
    permission_required = 'employees.add_employee'
    template_name = 'employees/employee_form.html'
    context_object_name = 'employee_details'
    redirect_field_name = 'employees/employee_detail.html'
    model = models.Employee
    form_class = forms.EmployeeForm

    def dispatch(self, request, *args, **kwargs):
        """
        Overridden so we can make sure the `Employer` instance exists
        before going any further.
        """
        self.employer = get_object_or_404(models.Employer, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        if not self.request.user.has_perm('employees.add_employee'):
            raise HttpResponseForbidden()
        else:
            """
            Overridden to add the employer relation to the `Employee` instance.
            """
            form.instance.creator = self.request.user
            form.instance.record_status = "Created"
            form.instance.source = "Web App"

            email_addr = form.instance.email
            phone_num = form.instance.mobile_phone
            print(phone_num)

            #NOTIFY Employee
            notification = Notification()
            subscription_arn = notification.SubscribeEmployeeObj(phone_num)
            notification.TextEmployeeObj(subscription_arn)

            notification.EmailEmployeeObj(email_addr)

            form.instance.sms = "Initial notification sent"
            form.instance.emailer = "Initial notification sent"

            form.instance.employer = self.employer

            return super().form_valid(form)

#Pull from  backend system of record(SOR)
@permission_required("employees.add_employee")
@login_required
def BackendPull(request, pk):
        # fetch the object related to passed id

        employee_obj = get_object_or_404(Employee, pk = pk)

        api = ApiDomains()
        url = api.employee + "/" + "latest"
        payload={'ident': employee_obj.employeeid}
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

            #OVERRIDE THE OBJECT WITH API data
            obj.pk = int(json_data["LOCAL_ID"])
            obj.employeeid = json_data["EMPLOYEE_ID"]
            obj.ssn = json_data["SSN"]
            obj.name = json_data["NAME"]
            obj.name_html = misaka.html(obj.name)
            obj.gendercode = json_data["GENDERCODE"]
            obj.age = json_data["AGE"]
            obj.birthdate = json_data["BIRTHDATE"]
            obj.maritalstatus = json_data["MARITALSTATUS"]

            obj.home_address_line_1 = json_data["HOME_ADDRESS_LINE_1"]
            obj.home_address_line_2 = json_data["HOME_ADDRESS_LINE_2"]
            obj.home_city = json_data["HOME_CITY"]
            obj.home_state = json_data["HOME_STATE"]
            obj.home_zipcode = json_data["HOME_ZIPCODE"]

            obj.mail_address_line_1 = json_data["MAIL_ADDRESS_LINE_1"]
            obj.mail_address_line_2 = json_data["MAIL_ADDRESS_LINE_2"]
            obj.mail_city = json_data["MAIL_CITY"]
            obj.mail_state = json_data["MAIL_STATE"]
            obj.mail_zipcode = json_data["MAIL_ZIPCODE"]

            obj.work_address_line_1 = json_data["WORK_ADDRESS_LINE_1"]
            obj.work_address_line_2 = json_data["WORK_ADDRESS_LINE_2"]
            obj.work_city = json_data["WORK_CITY"]
            obj.work_state = json_data["WORK_STATE"]
            obj.work_zipcode = json_data["WORK_ZIPCODE"]

            obj.email = json_data["EMAIL"]
            obj.alternate_email = json_data["ALTERNATE_EMAIL"]

            obj.home_phone = json_data["HOME_PHONE"]
            obj.work_phone = json_data["WORK_PHONE"]
            obj.mobile_phone = json_data["MOBILE_PHONE"]

            obj.enrollment_method = json_data["ENROLLMENT_METHOD"]

            obj.employment_information = json_data["EMPLOYMENT_INFORMATION"]

            employer_id = json_data["EMPLOYER"]
            employer_obj = get_object_or_404(Employer, pk = employer_id)
            obj.employer = employer_obj

            obj.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            obj.employee_date = json_data["EMPLOYEE_DATE"]

            obj.sms = json_data["SMS"]
            obj.emailer = json_data["EMAILER"]
            obj.artefact = json_data["ARTEFACT"]

            obj.backend_SOR_connection = json_data["CONNECTION"]
            obj.response = json_data["RESPONSE"]
            obj.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj.record_status = json_data["RECORD_STATUS"]

            context = {'employee_details':obj}

            return render(request, "employees/employee_detail.html", context=context)



#Pull from  backend system of record(SOR)
@permission_required("employees.add_employee")
@login_required
def ListEmployeesHistory(request, pk):

                context ={}

                employee_obj = get_object_or_404(Employee, pk = pk)

                api = ApiDomains()
                url = api.employee + "/" + "history"

                payload={'ident': employee_obj.employeeid}

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
                     obj = Employee()
                      #dict_data.append(json.loads(json_data[ix]))
                     obj.pk = int(json_data[ix]["LOCAL_ID"])
                     obj.employeeid = json_data[ix]["EMPLOYEE_ID"]
                     obj.ssn = json_data[ix]["SSN"]
                     obj.name = json_data[ix]["NAME"]
                     obj.name_html = misaka.html(obj.name)
                     obj.gendercode = json_data[ix]["GENDERCODE"]
                     obj.age = json_data[ix]["AGE"]
                     obj.birthdate = json_data[ix]["BIRTHDATE"]
                     obj.maritalstatus = json_data[ix]["MARITALSTATUS"]

                     obj.home_address_line_1 = json_data[ix]["HOME_ADDRESS_LINE_1"]
                     obj.home_address_line_2 = json_data[ix]["HOME_ADDRESS_LINE_2"]
                     obj.home_city = json_data[ix]["HOME_CITY"]
                     obj.home_state = json_data[ix]["HOME_STATE"]
                     obj.home_zipcode = json_data[ix]["HOME_ZIPCODE"]

                     obj.mail_address_line_1 = json_data[ix]["MAIL_ADDRESS_LINE_1"]
                     obj.mail_address_line_2 = json_data[ix]["MAIL_ADDRESS_LINE_2"]
                     obj.mail_city = json_data[ix]["MAIL_CITY"]
                     obj.mail_state = json_data[ix]["MAIL_STATE"]
                     obj.mail_zipcode = json_data[ix]["MAIL_ZIPCODE"]

                     obj.work_address_line_1 = json_data[ix]["WORK_ADDRESS_LINE_1"]
                     obj.work_address_line_2 = json_data[ix]["WORK_ADDRESS_LINE_2"]
                     obj.work_city = json_data[ix]["WORK_CITY"]
                     obj.work_state = json_data[ix]["WORK_STATE"]
                     obj.work_zipcode = json_data[ix]["WORK_ZIPCODE"]

                     obj.email = json_data[ix]["EMAIL"]
                     obj.alternate_email = json_data[ix]["ALTERNATE_EMAIL"]

                     obj.home_phone = json_data[ix]["HOME_PHONE"]
                     obj.work_phone = json_data[ix]["WORK_PHONE"]
                     obj.mobile_phone = json_data[ix]["MOBILE_PHONE"]

                     obj.enrollment_method = json_data[ix]["ENROLLMENT_METHOD"]

                     obj.employment_information = json_data[ix]["EMPLOYMENT_INFORMATION"]

                     employer_id = json_data[ix]["EMPLOYER"]
                     employer_obj = get_object_or_404(Employer, pk = employer_id)
                     obj.employer = employer_obj

                     obj.creator = User.objects.get(pk=int(json_data[ix]["CREATOR"]))
                     obj.employee_date = json_data[ix]["EMPLOYEE_DATE"]

                     obj.sms = json_data[ix]["SMS"]
                     obj.emailer = json_data[ix]["EMAILER"]
                     obj.artefact = json_data[ix]["ARTEFACT"]

                     obj.backend_SOR_connection = json_data[ix]["CONNECTION"]
                     obj.response = json_data[ix]["RESPONSE"]
                     obj.commit_indicator = json_data[ix]["COMMIT_INDICATOR"]
                     obj.record_status = json_data[ix]["RECORD_STATUS"]

                     obj_data.append(obj)

                    context = {'object_list':obj_data}

                    return render(request, "employees/employee_list.html", context=context)

                    #mesg_obj = get_object_or_404(APICodes, http_response_code = 1000)
                    #status_message=mesg_obj.http_response_message
                    #mesg="1000" + " - " + status_message
                    # add form dictionary to context
                    #message={'messages':mesg}
                    #return render(request, "messages.html", context=message)


@permission_required("employees.add_employee")
@login_required
def RefreshEmployee(request, pk):
        # fetch the object related to passed id
        context ={}
        employee_obj = get_object_or_404(Employee, pk = pk)

        api = ApiDomains()
        url = api.employee + "/" + "refresh"

        payload={'ident': employee_obj.employeeid}

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
            obj1=Employee()

            #OVERRIDE THE OBJECT WITH API data
            obj1.pk = int(json_data["LOCAL_ID"])
            obj1.employeeid = json_data["EMPLOYEE_ID"]
            obj1.ssn = json_data["SSN"]
            obj1.name = json_data["NAME"]
            obj1.name_html = misaka.html(obj1.name)
            obj1.gendercode = json_data["GENDERCODE"]
            obj1.age = json_data["AGE"]
            obj1.birthdate = json_data["BIRTHDATE"]
            obj1.maritalstatus = json_data["MARITALSTATUS"]

            obj1.home_address_line_1 = json_data["HOME_ADDRESS_LINE_1"]
            obj1.home_address_line_2 = json_data["HOME_ADDRESS_LINE_2"]
            obj1.home_city = json_data["HOME_CITY"]
            obj1.home_state = json_data["HOME_STATE"]
            obj1.home_zipcode = json_data["HOME_ZIPCODE"]

            obj1.mail_address_line_1 = json_data["MAIL_ADDRESS_LINE_1"]
            obj1.mail_address_line_2 = json_data["MAIL_ADDRESS_LINE_2"]
            obj1.mail_city = json_data["MAIL_CITY"]
            obj1.mail_state = json_data["MAIL_STATE"]
            obj1.mail_zipcode = json_data["MAIL_ZIPCODE"]

            obj1.work_address_line_1 = json_data["WORK_ADDRESS_LINE_1"]
            obj1.work_address_line_2 = json_data["WORK_ADDRESS_LINE_2"]
            obj1.work_city = json_data["WORK_CITY"]
            obj1.work_state = json_data["WORK_STATE"]
            obj1.work_zipcode = json_data["WORK_ZIPCODE"]

            obj1.email = json_data["EMAIL"]
            obj1.alternate_email = json_data["ALTERNATE_EMAIL"]

            obj1.home_phone = json_data["HOME_PHONE"]
            obj1.work_phone = json_data["WORK_PHONE"]
            obj1.mobile_phone = json_data["MOBILE_PHONE"]

            obj1.enrollment_method = json_data["ENROLLMENT_METHOD"]

            obj1.employment_information = json_data["EMPLOYMENT_INFORMATION"]

            employer_id = json_data["EMPLOYER"]
            employer_obj = get_object_or_404(Employer, pk = employer_id)
            obj1.employer = employer_obj

            obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            obj1.employee_date = json_data["EMPLOYEE_DATE"]

            obj1.sms = json_data["SMS"]
            obj1.emailer = json_data["EMAILER"]
            obj1.artefact = json_data["ARTEFACT"]

            obj1.backend_SOR_connection = json_data["CONNECTION"]
            obj1.response = json_data["RESPONSE"]
            obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj1.record_status = json_data["RECORD_STATUS"]

            #Log events
            event = Event()
            event.EventTypeCode = "EER"
            event.EventSubjectId = obj1.employeeid
            event.EventSubjectName = obj1.name
            event.EventTypeReason = "Employee refreshed from ODS"
            event.source = "Web App"
            event.creator=obj1.creator
            event.save()

            obj1.save()

            context = {'employee_details':obj1}

            return render(request, "employees/employee_detail.html", context=context)



@login_required
@permission_required("employees.add_employee")
def VersionEmployee(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Employee, pk = pk)

    # pass the object as instance in form
    form = EmployeeForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            form.instance.creator = request.user
            form.instance.record_status = "Created"

            #Log events
            event = Event()
            event.EventTypeCode = "EEV"
            event.EventSubjectId = form.instance.employeeid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employee versioned"
            event.source = "Web App"
            event.creator=request.user
            event.save()

            form.save()
            return HttpResponseRedirect(reverse("employees:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "employees/employee_form.html", context)


class UpdateEmployee(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    #fields = ("name", "age")
    permission_required = 'employees.change_employee'
    template_name = 'employees/employee_form.html'
    #context_object_name = 'employee_details'
    redirect_field_name = 'employees/employee_detail.html'
    model = models.Employee
    form_class = forms.EmployeeForm

    def form_valid(self, form):

        if not self.request.user.has_perm('employees.change_employee'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            form.instance.record_status = "Updated"

            #Log events
            event = Event()
            event.EventTypeCode = "EEU"
            event.EventSubjectId = form.instance.employeeid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Employee updated"
            event.source = "Web App"
            event.creator=self.request.user
            event.save()

            return super().form_valid(form)


class DeleteEmployee(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView,):
    permission_required = 'employees.delete_employee'
    context_object_name = 'employee_details'
    form_class = forms.EmployeeForm
    model = models.Employee
    template_name = 'employees/employee_delete_confirm.html'
    success_url = reverse_lazy("employees:all")


    def delete(self, *args, **kwargs):
        messages.success(self.request, "Employee Deleted")
        return super().delete(*args, **kwargs)

    def form_valid(self, form):

        if not self.request.user.has_perm('employees.delete_employee'):
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


def SearchEmployeesForm(request):
    return render(request,'employees/employee_search_form.html')


class SearchEmployeesList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Employee
    template_name = 'employees/employee_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = models.Employee.objects.filter(
            Q(name__icontains=query) | Q(age__icontains=query) | Q(employeeid__icontains=query) | Q(home_address_line_1__icontains=query) | Q(home_city__icontains=query) | Q(home_state__icontains=query) | Q(home_zipcode__icontains=query) | Q(mail_address_line_1__icontains=query) | Q(mail_city__icontains=query) | Q(mail_state__icontains=query) | Q(mail_zipcode__icontains=query) | Q(work_address_line_1__icontains=query) | Q(work_city__icontains=query) | Q(work_state__icontains=query) | Q(work_zipcode__icontains=query) | Q(email__icontains=query) | Q(alternate_email__icontains=query) | Q(home_phone__icontains=query) | Q(work_phone__icontains=query) | Q(mobile_phone__icontains=query) | Q(enrollment_method__icontains=query) | Q(employment_information__icontains=query)
        )

        #change start for remote SearchEmployeesForm
        if not object_list:
            api = ApiDomains()
            url = api.employee + "/" + "refresh"

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
                obj1=Employee()

                #OVERRIDE THE OBJECT WITH API data
                obj1.pk = int(json_data["LOCAL_ID"])
                obj1.employeeid = json_data["EMPLOYEE_ID"]
                obj1.ssn = json_data["SSN"]
                obj1.name = json_data["NAME"]
                obj1.name_html = misaka.html(obj.name)
                obj1.gendercode = json_data["GENDERCODE"]
                obj1.age = json_data["AGE"]
                obj1.birthdate = json_data["BIRTHDATE"]
                obj1.maritalstatus = json_data["MARITALSTATUS"]

                obj1.home_address_line_1 = json_data["HOME_ADDRESS_LINE_1"]
                obj1.home_address_line_2 = json_data["HOME_ADDRESS_LINE_2"]
                obj1.home_city = json_data["HOME_CITY"]
                obj1.home_state = json_data["HOME_STATE"]
                obj1.home_zipcode = json_data["HOME_ZIPCODE"]

                obj1.mail_address_line_1 = json_data["MAIL_ADDRESS_LINE_1"]
                obj1.mail_address_line_2 = json_data["MAIL_ADDRESS_LINE_2"]
                obj1.mail_city = json_data["MAIL_CITY"]
                obj1.mail_state = json_data["MAIL_STATE"]
                obj1.mail_zipcode = json_data["MAIL_ZIPCODE"]

                obj1.work_address_line_1 = json_data["WORK_ADDRESS_LINE_1"]
                obj1.work_address_line_2 = json_data["WORK_ADDRESS_LINE_2"]
                obj1.work_city = json_data["WORK_CITY"]
                obj1.work_state = json_data["WORK_STATE"]
                obj1.work_zipcode = json_data["WORK_ZIPCODE"]

                obj1.email = json_data["EMAIL"]
                obj1.alternate_email = json_data["ALTERNATE_EMAIL"]

                obj1.home_phone = json_data["HOME_PHONE"]
                obj1.work_phone = json_data["WORK_PHONE"]
                obj1.mobile_phone = json_data["MOBILE_PHONE"]

                obj1.enrollment_method = json_data["ENROLLMENT_METHOD"]

                obj1.employment_information = json_data["EMPLOYMENT_INFORMATION"]

                employer_id = json_data["EMPLOYER"]
                employer_obj = get_object_or_404(Employer, pk = employer_id)
                obj1.employer = employer_obj

                obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
                obj1.employee_date = json_data["EMPLOYEE_DATE"]

                obj1.sms = json_data["SMS"]
                obj1.emailer = json_data["EMAILER"]
                obj1.artefact = json_data["ARTEFACT"]

                obj1.backend_SOR_connection = json_data["CONNECTION"]
                obj1.response = json_data["RESPONSE"]
                obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
                obj1.record_status = json_data["RECORD_STATUS"]

                obj1.save()

                object_remote_list = Employee.objects.filter(employeeid=query)
                print(object_remote_list)
                return object_remote_list

        else:
        #change end for remote SearchEmployeesForm

                return object_list


@permission_required("employees.add_employee")
@login_required
def BulkUploadEmployee(request, pk, *args, **kwargs):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.client('s3')
                    s3.download_file('intellidatastatic1', 'media/employees.csv', 'employees.csv')

                    with open('employees.csv', 'rt') as csv_file:
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
                                                      employeeid=row[1]
                                                      array2.append(employeeid)

                                                      ssn=row[2]
                                                      array2.append(ssn)

                                                       #validate name
                                                      name=row[3]
                                                      if name == "":
                                                          bad_ind = 1
                                                          description = "Name is mandatory"
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(name)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)

                                                      else:
                                                          array2.append(name)

                                                      slug=slugify(row[3])
                                                      #array2.append(slug)

                                                      gendercode=row[4]
                                                      array2.append(gendercode)

                                                      #validate age
                                                      age=int(row[5])
                                                      array1=[]
                                                      if age == "":
                                                          bad_ind=1
                                                          description = "Age must be numeric "
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(age)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      elif (age <= 0 or age >= 100):
                                                          bad_ind=1
                                                          description = "Age must be between 1 and 99 years "
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(age)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      else:
                                                           array2.append(age)

                                                      birthdate=row[6]
                                                      array2.append(birthdate)

                                                      maritalstatus=row[7]
                                                      array2.append(maritalstatus)

                                                      #validate address line 1
                                                      home_address_line_1=row[8]
                                                      array1=[]
                                                      if home_address_line_1 == "":
                                                          bad_ind = 1
                                                          description = "Home address line 1 is mandatory"
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(home_address_line_1)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      else:
                                                          array2.append(home_address_line_1)


                                                      #validate address line 2
                                                      home_address_line_2=row[9]
                                                      array2.append(home_address_line_2)

                                                           #validate city
                                                      home_city=row[10]
                                                      array1=[]
                                                      if home_city == "":
                                                           bad_ind = 1
                                                           description = "Home city is mandatory"
                                                           array1.append(serial)
                                                           array1.append(employeeid)
                                                           array1.append(name)
                                                           array1.append(home_city)
                                                           array1.append(description)
                                                           array1.append(pk)
                                                           array_bad.append(array1)
                                                      else:
                                                           array2.append(home_city)

                                                           #validate state
                                                      home_state=row[11]
                                                      array1=[]
                                                      if home_state == "":
                                                           bad_ind = 1
                                                           description = "Home state is mandatory"
                                                           array1.append(serial)
                                                           array1.append(employeeid)
                                                           array1.append(name)
                                                           array1.append(home_state)
                                                           array1.append(description)
                                                           array1.append(pk)
                                                           array_bad.append(array1)
                                                      else:
                                                          array2.append(home_state)

                                                          #validate zipcode
                                                      home_zipcode=row[12]
                                                      array1=[]
                                                      if home_zipcode == "":
                                                            bad_ind = 1
                                                            description = "Zipcode is mandatory"
                                                            array1.append(serial)
                                                            array1.append(employeeid)
                                                            array1.append(name)
                                                            array1.append(zipcode)
                                                            array1.append(description)
                                                            array1.append(pk)
                                                            array_bad.append(array1)
                                                      else:
                                                           array2.append(home_zipcode)

                                                      mail_address_line_1=row[13]
                                                      array2.append(mail_address_line_1)

                                                      mail_address_line_2=row[14]
                                                      array2.append(mail_address_line_2)

                                                      mail_city=row[15]
                                                      array2.append(mail_city)

                                                      mail_state=row[16]
                                                      array2.append(mail_state)

                                                      mail_zipcode=row[17]
                                                      array2.append(mail_zipcode)

                                                      work_address_line_1=row[18]
                                                      array2.append(work_address_line_1)

                                                      work_address_line_2=row[19]
                                                      array2.append(work_address_line_2)

                                                      work_city=row[20]
                                                      array2.append(work_city)

                                                      work_state=row[21]
                                                      array2.append(work_state)

                                                      work_zipcode=row[22]
                                                      array2.append(work_zipcode)


                                                            #validate email
                                                      email=row[23]
                                                      array1=[]
                                                      if email == "":
                                                          bad_ind=1
                                                          description = "Email is mandatory "
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(email)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      elif not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
                                                          bad_ind = 1
                                                          description = "Invalid email"
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(email)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      else:
                                                          array2.append(email)

                                                      alternate_email=row[24]
                                                      array2.append(alternate_email)

                                                      #validate phone
                                                      home_phone=row[25]
                                                      array2.append(home_phone)


                                                      work_phone=row[26]
                                                      array2.append(work_phone)

                                                      mobile_phone=row[27]
                                                      array1=[]
                                                      p=[]
                                                      p = mobile_phone
                                                      if p.isnumeric() == False:
                                                          bad_ind=1
                                                          description = "Mobile phone must be numbers "
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(mobile_phone)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      elif len(p) != (10 and 11):
                                                          print(len(p))
                                                          bad_ind=1
                                                          description = "Length of mobile phone number is not correct "
                                                          array1.append(serial)
                                                          array1.append(employeeid)
                                                          array1.append(name)
                                                          array1.append(mobile_phone)
                                                          array1.append(description)
                                                          array1.append(pk)
                                                          array_bad.append(array1)
                                                      else:
                                                           array2.append(mobile_phone)


                                                      enrollment_method=row[28]
                                                      array2.append(enrollment_method)

                                                      employment_information=row[29]
                                                      array2.append(employment_information)

                                                      employer=row[30]
                                                      array2.append(employer)


                                                      if bad_ind == 0:
                                                          array_good.append(array2)



                        # create good file
                    #with open('employees1.csv', 'w', newline='') as clean_file:
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
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employees1.csv')
                        s3.upload_fileobj(buff2, 'intellidatastatic1', 'media/employees1.csv')
                        print("Good File Upload Successful")

                    except FileNotFoundError:
                         print("The good file was not found")

                    except NoCredentialsError:
                         print("Credentials not available")


                           # create bad file
                    #with open('employee_error.csv', 'w', newline='') as error_file:
                    #       writer = csv.writer(error_file)
                    #       writer.writerows(array1)

                    buff3 = io.StringIO()

                    writer = csv.writer(buff3, dialect='excel', delimiter=',')
                    writer.writerows(array_bad)

                    buff4 = io.BytesIO(buff3.getvalue().encode())


                        # save bad file to S3
                    try:
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/employees_error.csv')
                        s3.upload_fileobj(buff4, 'intellidatastatic1', 'media/employees_error.csv')
                        print("Bad File Upload Successful")

                    except FileNotFoundError:
                        print("The bad file was not found")

                    except NoCredentialsError:
                        print("Credentials not available")

                    # load the employee table
                    s3.download_file('intellidatastatic1', 'media/employees1.csv', 'employees1.csv')

                    with open('employees1.csv', 'rt') as csv_file:
                        bulk_mgr = BulkCreateManager(chunk_size=20)
                        notification = Notification()
                        for row in csv.reader(csv_file):
                            if row[1] == "":
                                bulk_mgr.add(models.Employee(employeeid = str(uuid.uuid4())[26:36],
                                                          ssn=row[2],
                                                          name=row[3],
                                                          slug=slugify(row[3]),
                                                          gendercode=row[4],
                                                          age=int(row[5]),
                                                          birthdate=row[6],
                                                          maritalstatus=row[7],
                                                          home_address_line_1=row[8],
                                                          home_address_line_2=row[9],
                                                          home_city=row[10],
                                                          home_state=row[11],
                                                          home_zipcode=row[12],
                                                          mail_address_line_1=row[13],
                                                          mail_address_line_2=row[14],
                                                          mail_city=row[15],
                                                          mail_state=row[16],
                                                          mail_zipcode=row[17],
                                                          work_address_line_1=row[18],
                                                          work_address_line_2=row[19],
                                                          work_city=row[20],
                                                          work_state=row[21],
                                                          work_zipcode=row[22],
                                                          email=row[23],
                                                          alternate_email=row[24],
                                                          home_phone=row[25],
                                                          work_phone=row[26],
                                                          mobile_phone=row[27],
                                                          enrollment_method=row[28],
                                                          employment_information=row[29],
                                                          employer=get_object_or_404(models.Employer, pk=pk),
                                                          creator = request.user,
                                                          sms="Initial notification sent",
                                                          emailer="Initial notification sent",
                                                          source="Web App Bulk Upload",
                                                          record_status = "Created",
                                                          bulk_upload_indicator = "Y"
                                                          ))
                            else:
                                bulk_mgr.add(models.Employee(employeeid = row[1],
                                                          ssn=row[2],
                                                          name=row[3],
                                                          slug=slugify(row[3]),
                                                          gendercode=row[4],
                                                          age=int(row[5]),
                                                          birthdate=row[6],
                                                          maritalstatus=row[7],
                                                          home_address_line_1=row[8],
                                                          home_address_line_2=row[9],
                                                          home_city=row[10],
                                                          home_state=row[11],
                                                          home_zipcode=row[12],
                                                          mail_address_line_1=row[13],
                                                          mail_address_line_2=row[14],
                                                          mail_city=row[15],
                                                          mail_state=row[16],
                                                          mail_zipcode=row[17],
                                                          work_address_line_1=row[18],
                                                          work_address_line_2=row[19],
                                                          work_city=row[20],
                                                          work_state=row[21],
                                                          work_zipcode=row[22],
                                                          email=row[23],
                                                          alternate_email=row[24],
                                                          home_phone=row[25],
                                                          work_phone=row[26],
                                                          mobile_phone=row[27],
                                                          enrollment_method=row[28],
                                                          employment_information=row[29],
                                                          employer=get_object_or_404(models.Employer, pk=pk),
                                                          creator = request.user,
                                                          sms="Initial notification sent",
                                                          emailer="Initial notification sent",
                                                          source="Web App Bulk Upload",
                                                          record_status = "Created",
                                                          bulk_upload_indicator = "Y"
                                                          ))

                    with open('employees1.csv', 'rt') as csv_file:
                        for ix in csv.reader(csv_file):

                                #NOTIFY Employee
                                subscription_arn = notification.SubscribeEmployeeObj(ix[27])
                                notification.TextEmployeeObj(subscription_arn)

                                notification.EmailEmployeeObj(ix[23])

                        bulk_mgr.done()

                        # load the employee error table
                        s3.download_file('intellidatastatic1', 'media/employees_error.csv', 'employees_error.csv')

                        #Refresh Error table for concerned employer
                        EmployeeError.objects.filter(employer_id=pk).delete()

                        with open('employees_error.csv', 'rt') as csv_file:
                            bulk_mgr = BulkCreateManager(chunk_size=20)
                            for row1 in csv.reader(csv_file):
                                bulk_mgr.add(models.EmployeeError(serial = row1[0],
                                                          employeeid=row1[1],
                                                          name=row1[2],
                                                          errorfield=row1[3],
                                                          description=row1[4],
                                                          employer=get_object_or_404(models.Employer, pk=pk),
                                                          creator = request.user,
                                                          source="Web App Bulk Upload"
                                                          ))
                            bulk_mgr.done()


                    error_report = EmployeeErrorAggregate()
                    error_report.employer = get_object_or_404(Employer, pk=pk)

                    error_report.clean=Employee.objects.filter(employer_id=pk).count()
                    error_report.error=EmployeeError.objects.filter(employer_id=pk).count()

                    #distinct = EmployeeError.objects.filter(employer_id=pk).values('serial').annotate(serial_count=Count('serial')).filter(serial_count=1)
                    #records = EmployeeError.objects.filter(serial__in=[item['serial'] for item in distinct]).count()
                    #error_report.error=records


                    error_report.total=(error_report.clean + error_report.error)

                    #Refresh Error aggregate table for concerned employer
                    EmployeeErrorAggregate.objects.filter(employer_id=pk).delete()


                    error_report.save()

                    #Log events
                    event = Event()
                    event.EventTypeCode = "EEB"
                    event.EventSubjectId = "bulkemployees"
                    event.EventSubjectName = "Bulk processing"
                    event.EventTypeReason = "Employees uploaded in bulk"
                    event.source = "Web App"
                    event.creator=request.user
                    event.save()


                    return HttpResponseRedirect(reverse("employees:all"))



                    #return HttpResponseRedirect(reverse("employees:all"))

        else:
                            # add form dictionary to context
                    context["form"] = form

                    return render(request, "bulkuploads/bulkupload_form.html", context)



@permission_required("employees.add_employee")
@login_required
def BulkUploadEmployee_deprecated(request, pk, *args, **kwargs):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.client('s3')
                    s3.download_file('intellidatastatic1', 'media/employees1.csv', 'employees1.csv')

                    with open('employees1.csv', 'rt') as csv_file:
                        bulk_mgr = BulkCreateManager(chunk_size=20)
                        for row in csv.reader(csv_file):
                            bulk_mgr.add(models.Employee(employeeid = str(uuid.uuid4())[26:36],
                                                      name=row[1],
                                                      slug=slugify(row[1]),
                                                      age=int(row[2]),
                                                      address_line_1=row[3],
                                                      address_line_2=row[4],
                                                      city=row[5],
                                                      state=row[6],
                                                      zipcode=row[7],
                                                      email=row[8],
                                                      phone=row[9],
                                                      employer=get_object_or_404(models.Employer, pk=pk),
                                                      creator = request.user,
                                                      record_status = "Created",
                                                      bulk_upload_indicator = "Y"
                                                      ))
                        bulk_mgr.done()

                    return HttpResponseRedirect(reverse("employees:all"))

        else:
                            # add form dictionary to context
                    context["form"] = form

                    return render(request, "bulkuploads/bulkupload_form.html", context)


@permission_required("employees.add_employee")
@login_required
def BulkUploadSOR(request):

    array = Employee.objects.filter(bulk_upload_indicator='Y')
    serializer = EmployeeSerializer(array, many=True)
    json_array = serializer.data

    api = ApiDomains()
    url = api.employee + "/" + "upload"
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
        Employee.objects.filter(bulk_upload_indicator='Y').update(bulk_upload_indicator=" ")

        #Log events
        event = Event()
        event.EventTypeCode = "EEO"
        event.EventSubjectId = "employeeodsupload"
        event.EventSubjectName = "Bulk upload to ODS"
        event.EventTypeReason = "Employees uploaded to ODS in bulk"
        event.source = "Web App"
        event.creator=request.user
        event.save()

        return HttpResponseRedirect(reverse("employees:all"))


class ViewEmployeeErrorList(LoginRequiredMixin, generic.ListView):
    context_object_name = 'employee_error_list'
    model = models.EmployeeError
    template_name = 'employees/employee_error_list.html'

    #form_class = forms.employeeForm

    def get_queryset(self):
    #    return employee.objects.filter(employer=employer_name)
    #    return employee.objects.all
        #return models.employee.objects.prefetch_related('employer')
        return models.EmployeeError.objects.filter(employer_id=self.kwargs['pk'])



#Send for subscription
@permission_required("employees.add_employee")
@login_required
def SubscribeEmployee(request, pk):

    context ={}

    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:321504535921:intellidata-employee-communication-topic'

    obj = get_object_or_404(Employee, pk = pk)

    form = EmployeeForm(request.POST or None, instance = obj)

    if form.is_valid():
        number = str(form["mobile_phone"]).strip()
        number_array = number.split()
        number = number_array[3]
        number=number.split("=")[1]
        #to_email_address=to_email_address.strip(")
        number=number.replace('"', '')
        print("that is what I see " + number )
        #emailaddr = str(form["email"])

        # Add  Subscribers
        try:
            response = sns.subscribe(
                        TopicArn=topic_arn,
                        Protocol='SMS',
                        Endpoint=number
                       )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Subscription done!"),
            obj.sms = "Phone Number Subscribed On " + str(datetime.date.today())
        #form.emailer = "Email Notification Sent on " + str(datetime.date.today())
        form.save()
        return HttpResponseRedirect(reverse("employees:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "employees/employee_form.html", context)



@permission_required("employees.add_employee")
@login_required
def TextEmployee(request, pk):

    context = {}

    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:321504535921:intellidata-employee-communication-topic'

    message = "Enrollment complete"
    messageJSON = json.dumps({"message":message})

    obj = get_object_or_404(Employee, pk = pk)

    form = EmployeeForm(request.POST or None, instance = obj)

    if form.is_valid():

        try:
            response=sns.publish(
                        TopicArn=topic_arn,
                        Message=message
                     )

        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("SMS sent!"),
            obj.sms = "SMS Notification Sent on " + str(datetime.date.today())

        form.save()
        return HttpResponseRedirect(reverse("employees:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "employees/employee_form.html", context)



@permission_required("employees.add_employee")
@login_required
def EmailEmployee(request, pk):

    context = {}

    message = "Start Enrollment"
    messageJSON = json.dumps({"message":message})

    obj = get_object_or_404(Employee, pk = pk)

    form = EmployeeForm(request.POST or None, instance = obj)

    if form.is_valid():
        to_email = str(form["alternate_email"]).strip()
        to_email_array = to_email.split()
        to_email_value = to_email_array[3]
        to_email_address=to_email_value.split("=")[1]
        #to_email_address=to_email_address.strip(")
        to_email_address=to_email_address.replace('"', '')
        #to_email_address = "'{}'".format(to_email_address)

        #print("what we see is " + to_email_address)
        #to_email = 'svjt78@gmail.com'
        from_email = 'suvojit.dt@gmail.com'
            # Replace sender@example.com with your "From" address.
        # This address must be verified with Amazon SES.

        SENDER = from_email

        # Replace recipient@example.com with a "To" address. If your account
        # is still in the sandbox, this address must be verified.
        RECIPIENT = to_email_address

        # Specify a configuration set. If you do not want to use a configuration
        # set, comment the following variable, and the
        # ConfigurationSetName=CONFIGURATION_SET argument below.
        #CONFIGURATION_SET = "ConfigSet"

        # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
        AWS_REGION = "us-east-1"

        # The subject line for the email.
        SUBJECT = "Enrollment"

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = ("Start Enrollment\r\n"
                     "Enrollment complete "
                    )

        # The HTML body of the email.
        BODY_HTML = """<html>
        <head></head>
        <body>
          <h1>Start Enrollment</h1>
          <p>This email was sent with
            <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
            <a href='https://aws.amazon.com/sdk-for-python/'>
              AWS SDK for Python (Boto)</a>.</p>
        </body>
        </html>
                    """

        # The character encoding for the email.
        CHARSET = "UTF-8"

        # Create a new SES resource and specify a region.
        client = boto3.client('ses',region_name=AWS_REGION)

        # Try to send the email.
        try:
            #Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                #ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
            obj.emailer = "Email Notification Sent on " + str(datetime.date.today())

        #form.emailer = "Email Notification Sent on " + str(datetime.date.today())
        form.save()
        return HttpResponseRedirect(reverse("employees:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "employees/employee_form.html", context)


#rest API call
@api_view(['GET', 'POST'])
def EmployeeList(request):

    if request.method == 'GET':
        contacts = Employee.objects.all()
        serializer = EmployeeSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = EmployeeSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        employee = Employee()
        event = Event()

        if serializer.data["employeeid"] == '':
            employee.employeeid = str(uuid.uuid4())[26:36]
            event.EventTypeReason = "New employee received via API"
        else:
            employee.employeeid = serializer.data["employeeid"]
            event.EventTypeReason = "Employee added via API"

        employee.ssn = serializer.data["ssn"]
        employee.name = serializer.data["name"]
        employee.slug=slugify(employee.name)

        employee.gendercode = serializer.data["gendercode"]
        employee.age = serializer.data["age"]
        employee.birthdate = serializer.data["birthdate"]
        employee.maritalstatus = serializer.data["maritalstatus"]

        employee.home_address_line_1 = serializer.data["home_address_line_1"]
        employee.home_address_line_2 = serializer.data["home_address_line_2"]
        employee.home_city = serializer.data["home_city"]
        employee.home_state = serializer.data["home_state"]
        employee.home_zipcode = serializer.data["home_zipcode"]

        employee.mail_address_line_1 = serializer.data["mail_address_line_1"]
        employee.mail_address_line_2 = serializer.data["mail_address_line_2"]
        employee.mail_city = serializer.data["mail_city"]
        employee.mail_state = serializer.data["mail_state"]
        employee.mail_zipcode = serializer.data["mail_zipcode"]

        employee.work_address_line_1 = serializer.data["work_address_line_1"]
        employee.work_address_line_2 = serializer.data["work_address_line_2"]
        employee.work_city = serializer.data["work_city"]
        employee.work_state = serializer.data["work_state"]
        employee.work_zipcode = serializer.data["work_zipcode"]

        employee.email = serializer.data["email"]
        employee.alternate_email = serializer.data["alternate_email"]

        employee.home_phone = serializer.data["home_phone"]
        employee.work_phone = serializer.data["work_phone"]
        employee.mobile_phone = serializer.data["mobile_phone"]

        employee.enrollment_method = serializer.data["enrollment_method"]
        employee.employment_information = serializer.data["employment_information"]

        employee.employer = get_object_or_404(Employer, pk=serializer.data["employer"])

        employee.source = "API Call"

        employee.creator = get_object_or_404(User, pk=serializer.data["creator"])
        #transmission.create_date = serializer.data["create_date"]
        employee.backend_SOR_connection = "Disconnected"
        employee.response = ""
        employee.commit_indicator = "Not Committed"
        employee.record_status = ""

        #Log events

        event.EventTypeCode = "EEW"
        event.EventSubjectId = employee.employeeid
        event.EventSubjectName = employee.name
        event.source = "API Call"
        event.creator=employee.creator
        event.save()

        employee.save()
        return Response(serializer.data)

    #if serializer.is_valid():
    #    serializer.save()

    #    return Response(serializer.data, status=status.HTTP_201_CREATED)

    #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#rest API call
@api_view(['GET', 'POST'])
def EmployeeListByEmployer(request, pk):

    if request.method == 'GET':
        contacts = Employee.objects.filter(employer_id = pk)
        serializer = EmployeeSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = EmployeeSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        employee = Employee()
        event = Event()

        if serializer.data["employeeid"] == '':
            employee.employeeid = str(uuid.uuid4())[26:36]
            event.EventTypeReason = "New employee received via API"
        else:
            employee.employeeid = serializer.data["employeeid"]
            event.EventTypeReason = "Employee added via API"
        #transmission.transmissionid = serializer.data["transmissionid"]
        employee.ssn = serializer.data["ssn"]
        employee.name = serializer.data["name"]
        employee.slug=slugify(employee.name),

        employee.gendercode = serializer.data["gendercode"]
        employee.age = serializer.data["age"]
        employee.birthdate = serializer.data["birthdate"]
        employee.maritalstatus = serializer.data["maritalstatus"]

        employee.home_address_line_1 = serializer.data["home_address_line_1"]
        employee.home_address_line_2 = serializer.data["home_address_line_2"]
        employee.home_city = serializer.data["home_city"]
        employee.home_state = serializer.data["home_state"]
        employee.home_zipcode = serializer.data["home_zipcode"]

        employee.mail_address_line_1 = serializer.data["mail_address_line_1"]
        employee.mail_address_line_2 = serializer.data["mail_address_line_2"]
        employee.mail_city = serializer.data["mail_city"]
        employee.mail_state = serializer.data["mail_state"]
        employee.mail_zipcode = serializer.data["mail_zipcode"]

        employee.work_address_line_1 = serializer.data["work_address_line_1"]
        employee.work_address_line_2 = serializer.data["work_address_line_2"]
        employee.work_city = serializer.data["work_city"]
        employee.work_state = serializer.data["work_state"]
        employee.work_zipcode = serializer.data["work_zipcode"]

        employee.email = serializer.data["email"]
        employee.alternate_email = serializer.data["alternate_email"]

        employee.home_phone = serializer.data["home_phone"]
        employee.work_phone = serializer.data["work_phone"]
        employee.mobile_phone = serializer.data["mobile_phone"]

        employee.enrollment_method = serializer.data["enrollment_method"]
        employee.employment_information = serializer.data["employment_information"]

        employee.employer = get_object_or_404(Employer, pk=serializer.data["employer"])

        employee.source = "API Call"

        employee.creator = get_object_or_404(User, pk=serializer.data["creator"])
        #transmission.create_date = serializer.data["create_date"]
        employee.backend_SOR_connection = "Disconnected"
        employee.response = ""
        employee.commit_indicator = "Not Committed"
        employee.record_status = ""

        #Log events
        event.EventTypeCode = "EEW"
        event.EventSubjectId = employee.employeeid
        event.EventSubjectName = employee.name
        event.source = "API Call"
        event.creator=employee.creator
        event.save()

        employee.save()
        return Response(serializer.data)

    #if serializer.is_valid():
    #    serializer.save()

    #    return Response(serializer.data, status=status.HTTP_201_CREATED)

    #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




#notify employees in email and text message on phone

#publish message

@permission_required("employees.add_employee")
@login_required
def Notifyemployee_deprecated(request, pk):

    context = {}

    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:215632354817:intellidata_notify_topic'

    message = "Start Enrollment"
    messageJSON = json.dumps({"message":message})

    obj = get_object_or_404(Employee, pk = pk)

    form = EmployeeForm(request.POST or None, instance = obj)

    if form.is_valid():
        number = str(form["phone"])
        email = str(form["email"])

        sns.subscribe(
                TopicArn=topic_arn,
                Protocol='Email-JSON',
                Endpoint="svjt78@gmail.com"
        )

        sns.publish(
            TopicArn=topic_arn,
            Message=messageJSON
        )

    #number = '+17702233322'
    #sns.publish(PhoneNumber = number, Message='example text message' )

    # Add SMS Subscribers


        form["sms"] = "SMS Notification Sent on " + str(datetime.date.today())
        form["emailer"] = "Email Notification Sent on " + str(datetime.date.today())
        form.save()
        return HttpResponseRedirect(reverse("employees:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "employees/employee_form.html", context)


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
