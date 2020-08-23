from django.conf.urls import url

from . import views

app_name = 'events'

urlpatterns = [
    url(r"^$", views.ListEvents.as_view(), name="all"),
    url(r"^ods/history/(?P<pk>\d+)/$", views.ListEventsHistory, name="history"),
    url(r"^ods/refresh/(?P<pk>\d+)/$", views.RefreshEvent, name="refresh"),
    url(r"^new/$", views.CreateEvent.as_view(), name="create"),
    url(r"^bulkupload/$",views.BulkUploadEvent,name="bulk"),
    url(r"^bulkuploadods/$",views.BulkUploadSOR,name="bulksor"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionEvent, name="version"),
    url(r"^ods/pull/(?P<pk>\d+)/$",views.BackendPull, name="backendpull"),
    url(r"^search/$", views.SearchEventsForm, name="search"),
    url(r"^search/results/$", views.SearchEventsList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleEvent.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateEvent.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteEvent.as_view(),name="delete"),
    url(r"^rest/eventlist/$",views.EventList, name="rest"),
    url(r"^event/error/$",views.ViewEventErrorList.as_view(), name='feederrors'),
    url(r"^(?P<pk>\d+)/employers/show/$", views.ShowEmployersList.as_view(), name="show_employers"),
]
