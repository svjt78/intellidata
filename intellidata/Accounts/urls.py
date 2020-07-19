from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views
from django.urls import reverse

app_name = 'Accounts'

urlpatterns = [
    url(r"login/$", auth_views.LoginView.as_view(template_name="Accounts/login.html"),name='login'),
    url(r"logout/$", auth_views.LogoutView.as_view(), name="logout"),
    url(r"signup/$", views.SignUp.as_view(), name="signup"),
    url(r"editprofile/(?P<pk>\d+)/$", views.EditProfile.as_view(), name="editprofile"),
]
