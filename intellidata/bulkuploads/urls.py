from django.conf.urls import url

from . import views

app_name = 'bulkuploads'

urlpatterns = [
    url(r"^upload/$", views.SingleFile, name="upload"),

]
