from django.contrib.auth import login, logout
from django.contrib import auth
#from django.core.urlresolvers import reverse_lazy
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import UpdateView
from . import models
from . import forms
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from . import forms

class SignUp(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("login")
    template_name = "Accounts/signup.html"


class EditProfile(UpdateView):
    model = auth.models.User
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("login")
    template_name = "Accounts/signup.html"
