from django.conf.urls import url
from django.urls import reverse

from . import views

app_name = 'agreements'

urlpatterns = [
    url(r"^$", views.ListAgreements.as_view(), name="all"),
    url(r"^(?P<pk>\d+)/new/$", views.CreateAgreement.as_view(), name="create"),
    url(r"^search/$", views.SearchAgreementsForm, name="search"),
    url(r"^(?P<pk>\d+)/products/show/$", views.ShowAgreementsProduct.as_view(), name="manage_products"),
    url(r"^(?P<pk>\d+)/contracts/show/$", views.ShowContractsList.as_view(), name="show_contracts"),
    url(r"^search/results/$", views.SearchAgreementsList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleAgreement.as_view(),name="single"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionAgreement,name="version"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateAgreement.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteAgreement.as_view(),name="delete"),
    url(r"^rest/agreementlist/$",views.AgreementList, name="rest"),
    url(r"^(?P<pk>\d+)/rest/agreementlist/$",views.AgreementListByEmployer, name="byemployer"),
    ]
