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
from mandatories.models import Mandatory
from mandatories.forms import MandatoryForm
import csv
import os.path
from os import path
import uuid

import boto3
import requests

# Create your views here.

class SingleMandatory(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'mandatory_details'
    model = models.Mandatory
    template_name = 'mandatories/mandatory_details.html'


class ListMandatories(LoginRequiredMixin, generic.ListView):
    model = models.Mandatory
    template_name = 'mandatories/mandatory_list.html'

    def get_queryset(self):
        return models.Mandatory.objects.all()


class CreateMandatory(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'mandatories.add_mandatory'
    context_object_name = 'mandatory_details'
    redirect_field_name = 'mandatories/mandatory_list.html'
    form_class = forms.MandatoryForm
    model = models.Mandatory
    template_name = 'mandatories/mandatory_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('mandatories.add_mandatory'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            return super().form_valid(form)



@permission_required("mandatories.add_mandatory")
@login_required
def VersionMandatory(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Mandatory, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = MandatoryForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("mandatories:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "mandatories/mandatory_form.html", context)


class UpdateMandatory(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'mandatories.change_mandatory'
    context_object_name = 'mandatory_details'
    redirect_field_name = 'mandatories/mandatory_detail.html'
    form_class = forms.MandatoryForm
    model = models.Mandatory
    template_name = 'mandatories/mandatory_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('mandatories.change_mandatory'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteMandatory(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'mandatories.delete_mandatory'
    context_object_name = 'mandatory_details'
    form_class = forms.MandatoryForm
    model = models.Mandatory
    template_name = 'mandatories/mandatory_delete_confirm.html'
    success_url = reverse_lazy("mandatories:all")

    def form_valid(self, form):

        if not self.request.user.has_perm('mandatories.delete_mandatory'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
def SearchMandatoryForm(request):
    return render(request,'mandatories/mandatory_search_form.html')


class SearchMandatoryList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Mandatory
    template_name = 'mandatories/mandatory_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Mandatory.objects.filter(
            Q(attributes__icontains=query)
        )
        return object_list
