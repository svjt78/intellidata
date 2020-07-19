from django.contrib import messages
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member_count'] = Group.objects.annotate(association_count=Count('association'))
        print(context)
        return context['member_count']

class CreateGroup(LoginRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    login_url = '/login/'
    context_object_name = 'group_details'
    redirect_field_name = 'groups/group_list.html'
    form_class = forms.GroupForm
    model = models.Group
    template_name = 'groups/group_form.html'


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
