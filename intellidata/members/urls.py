from django.conf.urls import url

from . import views

app_name = 'members'

urlpatterns = [
    url(r"^$",views.ListMembers.as_view(),name='all'),
    url(r"^(?P<pk>\d+)/$",views.SingleMember.as_view(),name='single'),
    url(r"^version/(?P<pk>\d+)/$",views.VersionMember, name="version"),
    url(r"^search/$", views.SearchMembersForm, name="search"),
    url(r"^search/results/$", views.SearchMembersList.as_view(), name="search_results"),
    url(r"^(?P<pk>\d+)/create/$",views.CreateMember.as_view(),name='create'),
    url(r"^(?P<pk>\d+)/upload/$",views.BulkUploadMember, name='upload'),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateMember.as_view(),name='update'),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteMember.as_view(),name='delete'),
    url(r"^rest/$",views.MemberList, name="rest"),
]
