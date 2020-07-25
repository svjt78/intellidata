from django.conf.urls import url

from . import views

app_name = 'apicodes'

urlpatterns = [
    url(r"^$", views.ListCodes.as_view(), name="all"),
    url(r"^new/$", views.CreateCode.as_view(), name="create"),
    url(r"^bulkupload/$",views.BulkUploadAPICodes,name="bulk"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionCode, name="version"),
    url(r"^search/$", views.SearchAPICodesForm, name="search"),
    url(r"^search/results/$", views.SearchAPICodesList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleCode.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateCode.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteCode.as_view(),name="delete"),
]
