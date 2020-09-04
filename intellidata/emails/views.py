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
from . import models
from . import forms
from emails.models import Email
from bulkuploads.forms import BulkUploadForm
from bulkuploads.models import BulkUpload
from emails.forms import EmailForm
import csv
from employers.utils import BulkCreateManager
import os.path
from os import path
import uuid

import boto3
import requests

# Create your views here.

class SingleEmail(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'email_details'
    model = models.Email
    template_name = 'emails/email_detail.html'


class ListEmails(LoginRequiredMixin, generic.ListView):
    model = models.Email
    template_name = 'emails/email_list.html'

    def get_queryset(self):
        return models.Email.objects.all()


class CreateEmail(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'emails.add_email'
    context_object_name = 'email_details'
    redirect_field_name = 'emails/email_list.html'
    form_class = forms.EmailForm
    model = models.Email
    template_name = 'emails/email_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('emails.add_email'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            return super().form_valid(form)



@permission_required("emails.add_email")
@login_required
def VersionEmail(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Email, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = EmailForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("emails:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "emails/email_form.html", context)


class UpdateEmail(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'emails.change_email'
    context_object_name = 'email_details'
    redirect_field_name = 'emails/email_detail.html'
    form_class = forms.EmailForm
    model = models.Email
    template_name = 'emails/email_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('emails.change_email'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteEmail(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'emails.delete_email'
    context_object_name = 'email_details'
    form_class = forms.EmailForm
    model = models.Email
    template_name = 'emails/email_delete_confirm.html'
    success_url = reverse_lazy("emails:all")

    def form_valid(self, form):

        if not self.request.user.has_perm('emails.delete_email'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
def SearchEmailForm(request):
    return render(request,'emails/email_search_form.html')


class SearchEmailList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Email
    template_name = 'emails/email_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Email.objects.filter(
            Q(pk__icontains=query) | Q(name__icontains=query) | Q(type__icontains=query) | Q(description__icontains=query)
        )
        return object_list


@permission_required("emails.add_email")
@login_required
def BulkUploadEmail(request):

    context ={}

    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
                form.instance.creator = request.user
                form.save()

                #s3_resource = boto3.resource('s3')
                #s3_resource.Object("intellidatastatic", "media/products.csv").download_file(f'/tmp/{"products.csv"}') # Python 3.6+
                s3 = boto3.client('s3')
                s3.download_file('intellidatastatic', 'media/emails.csv', 'emails.csv')
                #with open('/tmp/{"products.csv"}', 'rt') as csv_file:
                with open('emails.csv', 'rt') as csv_file:
                    bulk_mgr = BulkCreateManager(chunk_size=20)
                    for row in csv.reader(csv_file):
                        bulk_mgr.add(models.Email(http_error_category=row[0],
                                                  http_response_code=row[1],
                                                  http_response_message=row[2]
                                                  ))
                    bulk_mgr.done()

                return HttpResponseRedirect(reverse("emails:all"))
    else:
            # add form dictionary to context
            context["form"] = form

            return render(request, "bulkuploads/bulkupload_form.html", context)
