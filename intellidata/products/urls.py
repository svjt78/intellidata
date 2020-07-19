from django.conf.urls import url

from . import views

app_name = 'products'

urlpatterns = [
    url(r"^$", views.ListProducts.as_view(), name="all"),
    url(r"^new/$", views.CreateProduct.as_view(), name="create"),
    url(r"^bulkupload/$",views.BulkUploadProduct,name="bulk"),
    url(r"^version/(?P<pk>\d+)/$",views.VersionProduct, name="version"),
    url(r"^search/$", views.SearchProductsForm, name="search"),
    url(r"^search/results/$", views.SearchProductsList.as_view(), name="search_results"),
    url(r"^posts/in/(?P<pk>\d+)/$",views.SingleProduct.as_view(),name="single"),
    url(r"^update/(?P<pk>\d+)/$",views.UpdateProduct.as_view(),name="update"),
    url(r"^delete/(?P<pk>\d+)/$",views.DeleteProduct.as_view(),name="delete"),
    url(r"^rest/$",views.ProductList, name="rest"),
]
