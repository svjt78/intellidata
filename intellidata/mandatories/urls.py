from django.conf.urls import url

from . import views

app_name = 'mandatories'

urlpatterns = [
    url(r"^$", views.ListMandatories.as_view(), name="all"),
    url(r"^new/$", views.CreateMandatory.as_view(), name="create"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionMandatory, name="version"),
    url(r"^search/$", views.SearchMandatoryForm, name="search"),
    url(r"^search/results/$", views.SearchMandatoryList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleMandatory.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateMandatory.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteMandatory.as_view(),name="delete"),
]
