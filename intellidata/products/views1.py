from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.decorators import user_passes_test
import time
from django.db.models import Q
from django.contrib.auth.mixins import(
    LoginRequiredMixin,
    PermissionRequiredMixin
)

from django.urls import reverse
from django.urls import reverse_lazy
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.views import generic
from django.db.models import Count
from groups.models import Group
from members.models import Member
from bulkuploads.models import BulkUpload
from products.models import Product
from . import models
from . import forms
from products.forms import ProductForm
from bulkuploads.forms import BulkUploadForm
import csv
from groups.utils import BulkCreateManager
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid

# For Rest rest_framework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from products.serializers import ProductSerializer

class SingleProduct(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'product_details'
    model = models.Product
    template_name = 'products/product_detail.html'

class ListProducts(LoginRequiredMixin, generic.ListView):
    model = models.Product
    template_name = 'products/product_list.html'

    def get_queryset(self):
        return models.Product.objects.all()
        #return models.Product.objects.get(user=request.user)


class CreateProduct(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
#    fields = ("name", "description")
    permission_required = 'products.add_product'
    context_object_name = 'product_details'
    redirect_field_name = 'products/product_list.html'
    form_class = forms.ProductForm
    model = models.Product
    template_name = 'products/product_form.html'

    def form_valid(self, form):
        if not self.request.user.has_perm('products.add_product'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            return super().form_valid(form)


@permission_required("products.add_product")
@login_required
def VersionProduct(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Product, pk = pk)
    #obj.photo.delete()
    #obj.photo.open(mode='rb')

    # pass the object as instance in form
    form = ProductForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            #form.photo = request.POST.get('photo', False)
            #form.photo = request.FILES['photo']
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("products:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "products/product_form.html", context)


class UpdateProduct(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'products.change_product'
    context_object_name = 'product_details'
    redirect_field_name = 'products/product_detail.html'
    form_class = forms.ProductForm
    model = models.Product
    template_name = 'products/product_form.html'

    def form_valid(self, form):

        if not self.request.user.has_perm('products.change_product'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)



class DeleteProduct(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'products.delete_product'
    context_object_name = 'product_details'
    form_class = forms.ProductForm
    model = models.Product
    template_name = 'products/product_delete_confirm.html'
    success_url = reverse_lazy("products:all")

    def form_valid(self, form):

        if not self.request.user.has_perm('products.delete_product'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
def SearchProductsForm(request):
    return render(request,'products/product_search_form.html')


class SearchProductsList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Product
    template_name = 'products/product_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = Product.objects.filter(
            Q(pk__icontains=query) | Q(name__icontains=query) | Q(type__icontains=query) | Q(description__icontains=query)
        )
        return object_list


@permission_required("products.add_product")
@login_required
def BulkUploadProduct(request):

    context ={}

    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
            form.instance.creator = request.user
            form.save()

            if not path.exists("intellidatastatic.s3.amazonaws.com/media/file/" + str(form['file'])):
                return render(request, "products/product_list.html", {'FileNotFound': True})
            else:
                with open("intellidatastatic.s3.amazonaws.com/media/file/" + str(form['file']), 'rt') as csv_file:
                    bulk_mgr = BulkCreateManager(chunk_size=20)
                    for row in csv.reader(csv_file):
                        bulk_mgr.add(models.Product(productid=row[0],
                                                  name=row[1],
                                                  slug=slugify(row[1]),
                                                  type=row[2],
                                                  description=row[3],
                                                  description_html = misaka.html(row[1]),
                                                  coverage_limit=row[4],
                                                  price_per_1000_units=row[5],
                                                  creator = request.user
                                                  ))
                    bulk_mgr.done()

            return HttpResponseRedirect(reverse("products:all"))
    else:
            # add form dictionary to context
            context["form"] = form

            return render(request, "bulkuploads/bulkupload_form.html", context)



@api_view(['GET', 'POST'])
def ProductList(request):

    if request.method == 'GET':
        contacts = Product.objects.all()
        serializer = ProductSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
