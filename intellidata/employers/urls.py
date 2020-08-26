
from django.conf.urls import url

from . import views

app_name = 'employers'

urlpatterns = [
    url(r"^$", views.ListEmployers.as_view(), name="all"),
    url(r"^create/$",views.CreateEmployer.as_view(),name='create'),
    url(r"^upload/standard/$",views.BulkUploadEmployer,name="bulk"),
    url(r"^upload/nonstandard/$",views.NonStdBulkUploadEmployer,name="spl_bulk"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionEmployer, name="version"),
    url(r"^search/$", views.SearchEmployersForm, name="search"),
    url(r"^search/results/$", views.SearchEmployersList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleEmployer.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateEmployer.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteEmployer.as_view(),name="delete"),
    url(r"^rest/employerlist/$",views.EmployerList, name="rest"),
    url(r"^(?P<pk>\d+)/rest/employerlist/$",views.EmployerListByTransmission, name="bytransmission"),
    url(r"^ods/history/(?P<pk>\d+)/$", views.ListEmployersHistory, name="history"),
    url(r"^ods/refresh/(?P<pk>\d+)/$", views.RefreshEmployer, name="refresh"),
    url(r"^bulkuploadods/$",views.BulkUploadSOR,name="bulksor"),
    url(r"^ods/pull/(?P<pk>\d+)/$",views.BackendPull, name="backendpull"),
    url(r"^employer/error/$",views.ViewEmployerErrorList.as_view(), name='feederrors'),
    url(r"^(?P<pk>\d+)/employees/show/$", views.ShowEmployeesList.as_view(), name="show_employees"),
    url(r"^(?P<pk>\d+)/agreements/show/$", views.ShowAgreementsList.as_view(), name="show_agreements"),

]
