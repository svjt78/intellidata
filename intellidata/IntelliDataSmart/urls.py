"""IntelliDataSmart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views
from controlcenter.views import controlcenter
from django.urls import reverse

urlpatterns = [
    url(r"^$", views.HomePage.as_view(), name="home"),
    url(r"^landing/$", views.TestPage.as_view(), name="test"),
    url(r"^thanks/$", views.ThanksPage.as_view(), name="thanks"),
    url(r"^gotoadmin/$", views.GotoAdmin, name="admin"),
    url(r"^admin/", admin.site.urls),
    url(r"^admin/dashboard/", controlcenter.urls),
    url(r"^accounts/", include("Accounts.urls", namespace="accounts")),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"^employees/", include("employees.urls", namespace="employees")),
    url(r"^employers/",include("employers.urls", namespace="employers")),
    url(r"^products/",include("products.urls", namespace="products")),
    url(r"^agreements/",include("agreements.urls", namespace="agreements")),
    url(r"^bulkuploads/",include("bulkuploads.urls", namespace="bulkuploads")),
    url(r"^apicodes/",include("apicodes.urls", namespace="apicodes")),
]
