from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
import time
from django.shortcuts import render
from django.contrib.auth.models import User
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
from groups.models import Group,GroupMember
from . import models
from . import forms
from members.models import Member
from groups.forms import GroupForm
import csv
from groups.utils import BulkCreateManager
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid
from bulkuploads.models import BulkUpload
from bulkuploads.forms import BulkUploadForm
import boto3

# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from groups.serializers import GroupSerializer

#class CreateGroup(LoginRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
#    model = Group

#class SingleGroup(generic.DetailView):
#    model = Group

#class ListGroups(generic.ListView):
#    model = Group


class SingleGroup(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'group_details'
    model = models.Group
    template_name = 'groups/group_detail.html'
    #form_class = forms.GroupForm

class ListGroups(LoginRequiredMixin, generic.ListView):
    model = models.Group
    template_name = 'groups/group_list.html'
    #form_class = forms.GroupForm

    def get_queryset(self):
        return Group.objects.all()
        #self.extra_context["member_count"] = Group.objects.annotate(association_count=Count('member_set'))

class CreateGroup(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'groups.add_group'
    context_object_name = 'group_details'
    redirect_field_name = 'groups/group_list.html'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('groups.add_group'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            return super().form_valid(form)


@permission_required("groups.add_group")
@login_required
def VersionGroup(request, pk):
    # dictionary for initial data with
    # field names as keys


        context ={}

        # fetch the object related to passed id
        obj = get_object_or_404(Group, pk = pk)

        # pass the object as instance in form
        form = GroupForm(request.POST or None, instance = obj)

        # save the data from the form and
        # redirect to detail_view
        if form.is_valid():
                obj.pk = int(round(time.time() * 1000))
                form.instance.creator = request.user
                form.save()
                return HttpResponseRedirect(reverse("groups:all"))

        else:

                # add form dictionary to context
                context["form"] = form

                return render(request, "groups/group_form.html", context)


class UpdateGroup(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
#    fields = ("name", "description")
    permission_required = 'groups.change_group'
    context_object_name = 'group_details'
    redirect_field_name = 'groups/group_detail.html'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('groups.change_group'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteGroup(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
#    fields = ("name", "description")
    permission_required = 'groups.delete_group'
    context_object_name = 'group_details'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_delete_confirm.html'
    success_url = reverse_lazy("groups:all")

    def form_valid(self, form):

        if not self.request.user.has_perm('groups.delete_group'):
            raise HttpResponseForbidden()
        else:
            return super().form_valid(form)


@login_required
def SearchGroupsForm(request):
    return render(request,'groups/group_search_form.html')


class SearchGroupsList(LoginRequiredMixin, generic.ListView):
    model = Group
    template_name = 'groups/group_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Group.objects.filter(
            Q(groupid__icontains=query) | Q(name__icontains=query) | Q(description__icontains=query) | Q(purpose__icontains=query)
        )
        return object_list


class ShowMembersList(LoginRequiredMixin, generic.ListView):
    model = Group
    template_name = 'members/member_list.html'

    def get_queryset(self): # new
        group = get_object_or_404(models.Group, pk=self.kwargs['pk'])
        object_list = group.member_set.all()

        return object_list

class ShowAgreementsList(LoginRequiredMixin, generic.ListView):
    model = Group
    template_name = 'agreements/agreement_list.html'

    def get_queryset(self): # new
        group = get_object_or_404(models.Group, pk=self.kwargs['pk'])
        object_list = group.group_set.all()

        return object_list


@permission_required("groups.add_group")
@login_required
def BulkUploadGroup(request):

    context ={}

    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
                form.instance.creator = request.user
                form.save()

                s3 = boto3.client('s3')
                s3.download_file('intellidatastatic', 'media/groups.csv', 'groups.csv')

                with open('/Users/suvojitdutta/Documents/PYTHON/PROJECTS/Docs/groups.csv', 'rt') as csv_file:
                    bulk_mgr = BulkCreateManager(chunk_size=20)
                    for row in csv.reader(csv_file):
                        bulk_mgr.add(models.Group(groupid = str(uuid.uuid4())[26:36],
                                                  name=row[0],
                                                  slug=slugify(row[0]),
                                                  description=row[1],
                                                  description_html = misaka.html(row[1]),
                                                  purpose=row[2],
                                                  creator = request.user
                                                  ))
                    bulk_mgr.done()

                return HttpResponseRedirect(reverse("groups:all"))

    else:
                # add form dictionary to context
                context["form"] = form

                return render(request, "bulkuploads/bulkupload_form.html", context)




@api_view(['GET', 'POST'])
def GroupList(request):

    if request.method == 'GET':
        contacts = Group.objects.all()
        serializer = GroupSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = GroupSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JoinGroup(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return reverse("groups:single",kwargs={"slug": self.kwargs.get("slug")})

    def get(self, request, *args, **kwargs):
        group = get_object_or_404(Group,slug=self.kwargs.get("slug"))

        try:
            GroupMember.objects.create(user=self.request.user,group=group)

        except IntegrityError:
            messages.warning(self.request,("Warning, already a member of {}".format(group.name)))

        else:
            messages.success(self.request,"You are now a member of the {} group.".format(group.name))

        return super().get(request, *args, **kwargs)


class LeaveGroup(LoginRequiredMixin, generic.RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return reverse("groups:single",kwargs={"slug": self.kwargs.get("slug")})

    def get(self, request, *args, **kwargs):

        try:

            membership = models.GroupMember.objects.filter(
                user=self.request.user,
                group__slug=self.kwargs.get("slug")
            ).get()

        except models.GroupMember.DoesNotExist:
            messages.warning(
                self.request,
                "You can't leave this group because you aren't in it."
            )
        else:
            membership.delete()
            messages.success(
                self.request,
                "You have successfully left this group."
            )
        return super().get(request, *args, **kwargs)
