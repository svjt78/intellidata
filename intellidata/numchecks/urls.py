from django.conf.urls import url

from . import views

app_name = 'numchecks'

urlpatterns = [
    url(r"^$", views.ListNumchecks.as_view(), name="all"),
    url(r"^new/$", views.CreateNumcheck.as_view(), name="create"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionNumcheck, name="version"),
    url(r"^search/$", views.SearchNumcheckForm, name="search"),
    url(r"^search/results/$", views.SearchNumcheckList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleNumcheck.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateNumcheck.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteNumcheck.as_view(),name="delete"),
]
