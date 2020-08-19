from django.conf.urls import url

from . import views

app_name = 'employees'

urlpatterns = [
    url(r"^$",views.ListEmployees.as_view(),name='all'),
    url(r"^(?P<pk>\d+)/$",views.SingleEmployee.as_view(),name='single'),
    url(r"^version/(?P<pk>\d+)/$",views.VersionEmployee, name="version"),
    url(r"^search/$", views.SearchEmployeesForm, name="search"),
    url(r"^search/results/$", views.SearchEmployeesList.as_view(), name="search_results"),
    url(r"^(?P<pk>\d+)/create/$",views.CreateEmployee.as_view(),name='create'),
    url(r"^(?P<pk>\d+)/employee/error/$",views.ViewEmployeeErrorList.as_view(), name='feederrors'),
    url(r"^(?P<pk>\d+)/upload/$",views.BulkUploadEmployee, name='upload'),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateEmployee.as_view(),name='update'),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteEmployee.as_view(),name='delete'),
    url(r"^email/(?P<pk>\d+)/$",views.EmailEmployee, name='email'),
    url(r"^subscribe/(?P<pk>\d+)/$",views.SubscribeEmployee, name='subscribe'),
    url(r"^text/(?P<pk>\d+)/$",views.TextEmployee, name='text'),
    url(r"^rest/employee/list/$",views.EmployeeList, name="rest"),
    url(r"^(?P<pk>\d+)/rest/employeelist/$",views.EmployeeListByEmployer, name="bygroup"),
    url(r"^ods/refresh/(?P<pk>\d+)/$", views.RefreshEmployee, name="refresh"),
    url(r"^loadods/$",views.BulkUploadSOR,name="bulksor"),
    url(r"^ods/pull/(?P<pk>\d+)/$",views.BackendPull, name="backendpull"),
    url(r"^ods/history/(?P<pk>\d+)/$", views.ListEmployeesHistory, name="history"),
]
