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
from numchecks.models import Numcheck
from numchecks.forms import NumcheckForm
import csv
import os.path
from os import path
import uuid

import boto3
import requests

# Create your views here.

class SingleNumcheck(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'numcheck_details'
    model = models.Numcheck
    template_name = 'numchecks/numcheck_details.html'


class ListNumchecks(LoginRequiredMixin, generic.ListView):
    model = models.Numcheck
    template_name = 'numchecks/numcheck_list.html'

    def get_queryset(self):
        return models.Numcheck.objects.all()


class CreateNumcheck(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'numchecks.add_numcheck'
    context_object_name = 'numcheck_details'
    redirect_field_name = 'numchecks/numcheck_list.html'
    form_class = forms.NumcheckForm
    model = models.Numcheck
    template_name = 'numchecks/numcheck_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('numchecks.add_numcheck'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            return super().form_valid(form)



@permission_required("numchecks.add_numcheck")
@login_required
def VersionNumcheck(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Numcheck, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = NumcheckForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("numchecks:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "numchecks/numcheck_form.html", context)


class UpdateNumcheck(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'numchecks.change_numcheck'
    context_object_name = 'numcheck_details'
    redirect_field_name = 'numchecks/numcheck_detail.html'
    form_class = forms.NumcheckForm
    model = models.Numcheck
    template_name = 'numchecks/numcheck_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('numchecks.change_numcheck'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteNumcheck(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'numchecks.delete_numcheck'
    context_object_name = 'numcheck_details'
    form_class = forms.NumcheckForm
    model = models.Numcheck
    template_name = 'numchecks/numcheck_delete_confirm.html'
    success_url = reverse_lazy("numchecks:all")

    def form_valid(self, form):

        if not self.request.user.has_perm('numchecks.delete_numcheck'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
def SearchNumcheckForm(request):
    return render(request,'numchecks/numcheck_search_form.html')


class SearchNumcheckList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Numcheck
    template_name = 'numchecks/numcheck_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Numcheck.objects.filter(
            Q(attributes__icontains=query)
        )
        return object_list
