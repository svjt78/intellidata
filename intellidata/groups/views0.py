from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.mixins import(
    LoginRequiredMixin,
    PermissionRequiredMixin
)

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.views import generic
from django.db.models import Count
from groups.models import Group,GroupMember
from . import models
from . import forms
from members.models import Member
from groups.forms import GroupForm

#class CreateGroup(LoginRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
#    model = Group

#class SingleGroup(generic.DetailView):
#    model = Group

#class ListGroups(generic.ListView):
#    model = Group


class SingleGroup(generic.DetailView):
    context_object_name = 'group_details'
    model = models.Group
    template_name = 'groups/group_detail.html'
    #form_class = forms.GroupForm

class ListGroups(generic.ListView):
    model = models.Group
    template_name = 'groups/group_list.html'
    #form_class = forms.GroupForm

    def get_queryset(self):
        return Group.objects.all()
        #self.extra_context["member_count"] = Group.objects.annotate(association_count=Count('member_set'))

class CreateGroup(LoginRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    login_url = '/login/'
    context_object_name = 'group_details'
    redirect_field_name = 'groups/group_list.html'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_form.html'

    def form_valid(self, form):
        form.instance.creator = self.request.user

        return super().form_valid(form)


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
            return HttpResponseRedirect(reverse("groups:create"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "groups/group_form.html", context)


class UpdateGroup(LoginRequiredMixin, generic.UpdateView):
#    fields = ("name", "description")
    login_url = '/login/'
    context_object_name = 'group_details'
    redirect_field_name = 'groups/group_detail.html'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_form.html'


class DeleteGroup(LoginRequiredMixin, generic.DeleteView):
#    fields = ("name", "description")
    login_url = '/login/'
    context_object_name = 'group_details'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_delete_confirm.html'
    success_url = reverse_lazy("groups:all")


def SearchGroupsForm(request):
    return render(request,'groups/group_search_form.html')


class SearchGroupsList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = Group
    template_name = 'groups/group_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Group.objects.filter(
            Q(pk__icontains=query) | Q(name__icontains=query) | Q(description__icontains=query) | Q(purpose__icontains=query)
        )
        return object_list


class ShowMembersList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = Group
    template_name = 'members/member_list.html'

    def get_queryset(self): # new
        group = get_object_or_404(models.Group, pk=self.kwargs['pk'])
        object_list = group.member_set.all()

        return object_list



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
