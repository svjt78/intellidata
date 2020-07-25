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
from apicodes.models import APICodes
from bulkuploads.forms import BulkUploadForm
from bulkuploads.models import BulkUpload
from apicodes.forms import APICodesForm
import csv
from groups.utils import BulkCreateManager
import os.path
from os import path
import uuid

import boto3
import requests

# Create your views here.

class SingleCode(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'code_details'
    model = models.APICodes
    template_name = 'apicodes/code_detail.html'


class ListCodes(LoginRequiredMixin, generic.ListView):
    model = models.APICodes
    template_name = 'apicodes/code_list.html'

    def get_queryset(self):
        return models.APICodes.objects.all()


class CreateCode(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'apicodes.add_code'
    context_object_name = 'code_details'
    redirect_field_name = 'apicodes/product_list.html'
    form_class = forms.APICodesForm
    model = models.APICodes
    template_name = 'apicodes/code_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('apicodes.add_code'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            return super().form_valid(form)



@permission_required("apicodes.add_code")
@login_required
def VersionCode(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(APICode, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = APICodesForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("apicodes:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "apicodes/code_form.html", context)


class UpdateCode(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'apicodes.change_code'
    context_object_name = 'code_details'
    redirect_field_name = 'apicodes/code_detail.html'
    form_class = forms.APICodesForm
    model = models.APICodes
    template_name = 'apicodes/code_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('apicodes.change_code'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteCode(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'apicodes.delete_code'
    context_object_name = 'code_details'
    form_class = forms.APICodesForm
    model = models.APICodes
    template_name = 'apicodes/code_delete_confirm.html'
    success_url = reverse_lazy("apicodes:all")

    def form_valid(self, form):

        if not self.request.user.has_perm('apicodes.delete_code'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
def SearchAPICodesForm(request):
    return render(request,'apicodes/code_search_form.html')


class SearchAPICodesList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.APICodes
    template_name = 'apicodes/code_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = APICodes.objects.filter(
            Q(pk__icontains=query) | Q(name__icontains=query) | Q(type__icontains=query) | Q(description__icontains=query)
        )
        return object_list


@permission_required("apicodes.add_code")
@login_required
def BulkUploadAPICodes(request):

    context ={}

    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
                form.instance.creator = request.user
                form.save()

                #s3_resource = boto3.resource('s3')
                #s3_resource.Object("intellidatastatic", "media/products.csv").download_file(f'/tmp/{"products.csv"}') # Python 3.6+
                s3 = boto3.client('s3')
                s3.download_file('intellidatastatic', 'media/apicodes.csv', 'apicodes.csv')
                #with open('/tmp/{"products.csv"}', 'rt') as csv_file:
                with open('apicodes.csv', 'rt') as csv_file:
                    bulk_mgr = BulkCreateManager(chunk_size=20)
                    for row in csv.reader(csv_file):
                        bulk_mgr.add(models.APICodes(http_error_category=row[0],
                                                  http_response_code=row[1],
                                                  http_response_message=row[2]
                                                  ))
                    bulk_mgr.done()

                return HttpResponseRedirect(reverse("apicodes:all"))
    else:
            # add form dictionary to context
            context["form"] = form

            return render(request, "bulkuploads/bulkupload_form.html", context)
