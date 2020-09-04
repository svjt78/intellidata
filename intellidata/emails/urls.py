from django.conf.urls import url

from . import views

app_name = 'emails'

urlpatterns = [
    url(r"^$", views.ListEmails.as_view(), name="all"),
    url(r"^new/$", views.CreateEmail.as_view(), name="create"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionEmail, name="version"),
    url(r"^search/$", views.SearchEmailForm, name="search"),
    url(r"^search/results/$", views.SearchEmailList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleEmail.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateEmail.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteEmail.as_view(),name="delete"),
]
