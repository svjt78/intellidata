from django.contrib import messages
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
from groups.models import Group
from members.models import Member
from . import models
from . import forms
from members.forms import MemberForm
from bulkuploads.models import BulkUpload
from bulkuploads.forms import BulkUploadForm
import boto3
import csv
from groups.utils import BulkCreateManager
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid

# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from members.serializers import MemberSerializer


class SingleMember(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'member_details'
    model = models.Member
    template_name = 'members/member_detail.html'
    #form_class = forms.MemberForm

class ListMembers(LoginRequiredMixin, generic.ListView):
    context_object_name = 'member_list'
    model = models.Member
    template_name = 'members/member_list.html'

    #form_class = forms.MemberForm

    def get_queryset(self):
    #    return Member.objects.filter(group=group_name)
    #    return Member.objects.all
        return models.Member.objects.filter( group_id=self.kwargs['pk'] )
        animal_id=self.kwargs['pk']


class CreateMember(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    #fields = ("name", "age")
    permission_required = 'members.add_member'
    template_name = 'members/member_form.html'
    context_object_name = 'member_details'
    redirect_field_name = 'members/member_detail.html'
    model = models.Member
    form_class = forms.MemberForm

    def dispatch(self, request, *args, **kwargs):
        """
        Overridden so we can make sure the `Group` instance exists
        before going any further.
        """
        self.group = get_object_or_404(models.Group, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        if not self.request.user.has_perm('members.add_member'):
            raise HttpResponseForbidden()
        else:
            """
            Overridden to add the group relation to the `Member` instance.
            """
            form.instance.group = self.group
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
@permission_required("members.add_member")
def VersionMember(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Member, pk = pk)

    # pass the object as instance in form
    form = MemberForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            g_pk = obj.group_id
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("members:all", kwargs={'pk': g_pk}))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "members/member_form.html", context)


class UpdateMember(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    #fields = ("name", "age")
    permission_required = 'members.change_member'
    template_name = 'members/member_form.html'
    #context_object_name = 'member_details'
    redirect_field_name = 'members/member_detail.html'
    model = models.Member
    form_class = forms.MemberForm

    def form_valid(self, form):

        if not self.request.user.has_perm('members.change_member'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteMember(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView,):
    permission_required = 'members.delete_member'
    context_object_name = 'member_details'
    form_class = forms.MemberForm
    model = models.Member
    template_name = 'members/member_delete_confirm.html'
    #success_url = reverse_lazy("members:all")


    def delete(self, *args, **kwargs):
        messages.success(self.request, "Member Deleted")
        return super().delete(*args, **kwargs)

    def form_valid(self, form):

        if not self.request.user.has_perm('members.delete_member'):
            raise HttpResponseForbidden()
        else:
            obj = get_object_or_404(Member, pk = self.pk)
            g_pk = obj.group_id
            #return super().form_valid(form)
            return HttpResponseRedirect(reverse("members:all", kwargs={'pk': g_pk}))


def SearchMembersForm(request):
    return render(request,'members/member_search_form.html')


class SearchMembersList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Member
    template_name = 'members/member_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = models.Member.objects.filter(
            Q(name__icontains=query) | Q(age__icontains=query)
        )
        return object_list


@permission_required("members.add_member")
@login_required
def BulkUploadMember(request, pk, *args, **kwargs):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.client('s3')
                    s3.download_file('intellidatastatic', 'media/members.csv', 'members.csv')

                    with open('members.csv', 'rt') as csv_file:
                        bulk_mgr = BulkCreateManager(chunk_size=20)
                        for row in csv.reader(csv_file):
                            bulk_mgr.add(models.Member(memberid = str(uuid.uuid4())[26:36],
                                                      name=row[0],
                                                      slug=slugify(row[0]),
                                                      age=int(row[1]),
                                                      email=row[2],
                                                      phone=row[3],
                                                      group=get_object_or_404(models.Group, pk=pk),
                                                      creator = request.user
                                                      ))
                        bulk_mgr.done()

                    return HttpResponseRedirect(reverse("members:all", kwargs={'pk': pk}))

        else:
                            # add form dictionary to context
                    context["form"] = form

                    return render(request, "bulkuploads/bulkupload_form.html", context)


@api_view(['GET', 'POST'])
def MemberList(request):

    if request.method == 'GET':
        #contacts = Member.objects.all()
        contacts = Member.objects.all()
        serializer = MemberSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = MemberSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
