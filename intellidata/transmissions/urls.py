from django.conf.urls import url

from . import views

app_name = 'transmissions'

urlpatterns = [
    url(r"^$", views.ListTransmissions.as_view(), name="all"),
    url(r"^ods/history/(?P<pk>\d+)/$", views.ListTransmissionsHistory, name="history"),
    url(r"^ods/refresh/(?P<pk>\d+)/$", views.RefreshTransmission, name="refresh"),
    url(r"^new/$", views.CreateTransmission.as_view(), name="create"),
    url(r"^bulkupload/$",views.BulkUploadTransmission,name="bulk"),
    url(r"^bulkuploadods/$",views.BulkUploadSOR,name="bulksor"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionTransmission, name="version"),
    url(r"^ods/pull/(?P<pk>\d+)/$",views.BackendPull, name="backendpull"),
    url(r"^search/$", views.SearchTransmissionsForm, name="search"),
    url(r"^search/results/$", views.SearchTransmissionsList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleTransmission.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateTransmission.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteTransmission.as_view(),name="delete"),
    url(r"^rest/Transmissionlist/$",views.TransmissionList, name="rest"),
    url(r"^Transmission/error/$",views.ViewTransmissionErrorList.as_view(), name='feederrors'),
    url(r"^(?P<pk>\d+)/employers/show/$", views.ShowEmployersList.as_view(), name="show_employers"),
]
