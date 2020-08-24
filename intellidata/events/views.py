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
from employees.models import Employee
from django.contrib.auth.models import User
from bulkuploads.models import BulkUpload
from apicodes.models import APICodes
from events.models import Event
from . import models
from . import forms
from events.forms import EventForm
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

import boto3
import requests
import json
import re
from botocore.exceptions import NoCredentialsError
import io
from django.db.models import Count


class SingleEvent(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'event_details'
    model = models.Event
    template_name = 'events/event_detail.html'

class ListEvents(LoginRequiredMixin, generic.ListView):
    model = models.Event
    template_name = 'events/event_list.html'

    def get_queryset(self):
        return models.Event.objects.all()
        #return models.event.objects.get(user=request.user)


class CreateEvent(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'events.add_event'
    context_object_name = 'event_details'
    redirect_field_name = 'events/event_list.html'
    form_class = forms.EventForm
    model = models.Event
    template_name = 'events/event_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('events.add_event'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            form.instance.record_status = "Created"
            form.instance.source = "Web App"

            return super().form_valid(form)


#Pull from  backend system of record(SOR)
@permission_required("events.add_event")
@login_required
def BackendPull(request, pk):
        # fetch the object related to passed id
        #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataeventAPI/latest'

        prod_obj = get_object_or_404(Event, pk = pk)

        api = ApiDomains()
        url = api.event + "/" + "latest"
        payload={'ident': prod_obj.eventid}
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
            #obj = get_object_or_404(Event, pk = json_data["LOCAL_ID"])

            # pass the object as instance in form
            #form = EventForm(request.POST or None, instance = obj)

            #OVERRIDE THE OBJECT WITH API data
            obj.pk = int(json_data["LOCAL_ID"])
            obj.eventid = json_data["EVENT_ID"]
            obj.EventTypeCode = json_data["EVENT_TYPE_CODE"]
            obj.EventSubjectId = json_data["EVENT_SUBJECT_ID"]
            obj.EventSubjectName = json_data["EVENT_SUBJECT_NAME"]
            obj.EventTypeReason = json_data["EVENT_TYPE_REASON"]

            obj.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj.EventDate = json_data["EVENT_DATE"]
            obj.TransactionDate = json_data["TRANSACTION_DATE"]

            obj.backend_SOR_connection = json_data["CONNECTION"]
            obj.response = json_data["RESPONSE"]
            obj.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj.record_status = json_data["RECORD_STATUS"]

            context = {'event_details':obj}

            return render(request, "events/event_detail.html", context=context)



#Pull from  backend system of record(SOR)
@permission_required("events.add_event")
@login_required
def ListEventsHistory(request, pk):

                context ={}

                prod_obj = get_object_or_404(Event, pk = pk)

                api = ApiDomains()
                url = api.event + "/" + "history"
                #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataeventAPI/history'
                payload={'ident': prod_obj.eventid}

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
                     obj = Event()
                      #dict_data.append(json.loads(json_data[ix]))
                     obj.pk = int(json_data[ix]["LOCAL_ID"])
                     obj.eventid = json_data[ix]["EVENT_ID"]
                     obj.EventTypeCode = json_data[ix]["EVENT_TYPE_CODE"]
                     obj.EventSubjectId = json_data[ix]["EVENT_SUBJECT_ID"]
                     obj.EventSubjectName = json_data[ix]["EVENT_SUBJECT_NAME"]
                     obj.EventTypeReason = json_data[ix]["EVENT_TYPE_REASON"]

                     obj.creator = User.objects.get(pk=int(json_data[ix]["CREATOR"]))
                     #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
                     obj.EventDate = json_data[ix]["EVENT_DATE"]
                     obj.TransactionDate = json_data[ix]["TRANSACTION_DATE"]

                     obj.backend_SOR_connection = json_data[ix]["CONNECTION"]
                     obj.response = json_data[ix]["RESPONSE"]
                     obj.commit_indicator = json_data[ix]["COMMIT_INDICATOR"]
                     obj.record_status = json_data[ix]["RECORD_STATUS"]

                     obj_data.append(obj)

                    context = {'object_list':obj_data}

                    return render(request, "events/event_list.html", context=context)

                    #mesg_obj = get_object_or_404(APICodes, http_response_code = 1000)
                    #status_message=mesg_obj.http_response_message
                    #mesg="1000" + " - " + status_message
                    # add form dictionary to context
                    #message={'messages':mesg}
                    #return render(request, "messages.html", context=message)


@permission_required("events.add_event")
@login_required
def RefreshEvent(request, pk):
        # fetch the object related to passed id
        context ={}
        prod_obj = get_object_or_404(Event, pk = pk)

        api = ApiDomains()
        url = api.event + "/" + "refresh"
        #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataeventAPI/history'
        payload={'ident': prod_obj.eventid}

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
            obj1=Event()

            #OVERRIDE THE OBJECT WITH API data
            obj1.pk = int(json_data["LOCAL_ID"])
            obj1.eventid = json_data["EVENT_ID"]
            obj1.EventTypeCode = json_data["EVENT_TYPE_CODE"]
            obj1.EventSubjectId = json_data["EVENT_SUBJECT_ID"]
            obj1.EventSubjectName = json_data["EVENT_SUBJECT_NAME"]
            obj1.EventTypeReason = json_data["EVENT_TYPE_REASON"]

            obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj1.EventDate = json_data["EVENT_DATE"]
            obj1.TransactionDate = json_data["TRANSACTION_DATE"]

            obj1.backend_SOR_connection = json_data["CONNECTION"]
            obj1.response = json_data["RESPONSE"]
            obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj1.record_status = json_data["RECORD_STATUS"]

            obj1.save()

            context = {'event_details':obj1}

            return render(request, "events/event_detail.html", context=context)


@permission_required("events.add_event")
@login_required
def VersionEvent(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Event, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = EventForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.instance.record_status = "Created"
            form.save()
            return HttpResponseRedirect(reverse("events:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "events/event_form.html", context)


class UpdateEvent(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'events.change_event'
    context_object_name = 'event_details'
    redirect_field_name = 'events/event_detail.html'
    form_class = forms.EventForm
    model = models.Event
    template_name = 'events/event_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('events.change_event'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            form.instance.record_status = "Updated"
            return super().form_valid(form)


class DeleteEvent(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'events.delete_event'
    context_object_name = 'event_details'
    form_class = forms.EventForm
    model = models.Event
    template_name = 'events/event_delete_confirm.html'
    success_url = reverse_lazy("events:all")

    def form_valid(self, form):
        print("hello")
        if not self.request.user.has_perm('events.delete_event'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
def SearchEventsForm(request):
    return render(request,'events/event_search_form.html')


class SearchEventsList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Event
    template_name = 'events/event_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Event.objects.filter(
            Q(eventid__icontains=query) | Q(EventTypeCode__icontains=query) | Q(EventTypeReason__icontains=query)
        )

        #change start for remote SearcheventsForm
        if not object_list:
            api = ApiDomains()
            url = api.event + "/" + "refresh"
            #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataeventAPI/history'
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
                obj1=Event()

                #OVERRIDE THE OBJECT WITH API data
                obj1.pk = int(json_data["LOCAL_ID"])
                obj1.eventid = json_data["EVENT_ID"]
                obj1.EventTypeCode = json_data["EVENT_TYPE_CODE"]
                obj1.EventSubjectId = json_data["EVENT_SUBJECT_ID"]
                obj1.EventSubjectName = json_data["EVENT_SUBJECT_NAME"]
                obj1.EventTypeReason = json_data["EVENT_TYPE_REASON"]

                obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
                #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
                obj1.EventDate = json_data["EVENT_DATE"]
                obj1.TransactionDate = json_data["TRANSACTION_DATE"]

                obj1.backend_SOR_connection = json_data["CONNECTION"]
                obj1.response = json_data["RESPONSE"]
                obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
                obj1.record_status = json_data["RECORD_STATUS"]

                obj1.save()



                #obj_data.append(obj1)
                #print(obj_data)

                #context = {'object_list':obj_data}

                #return render(self.request, "eventevents/event_search_list.html", context=context)
                object_remote_list = Event.objects.filter(eventid=query)
                print(object_remote_list)
                return object_remote_list

        else:
        #change end for remote SearcheventsForm

            return object_list


@permission_required("events.add_event")
@login_required
def BulkUploadSOR(request):

    array = Event.objects.filter(bulk_upload_indicator='Y')
    serializer = EventSerializer(array, many=True)
    json_array = serializer.data

    api = ApiDomains()
    url = api.event + "/" + "upload"
    #url='https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataeventAPI'
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
        Event.objects.filter(bulk_upload_indicator='Y').update(bulk_upload_indicator=" ")
        return HttpResponseRedirect(reverse("events:all"))


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
