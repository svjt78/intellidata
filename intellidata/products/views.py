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
from employers.models import Employer
from employees.models import Employee
from django.contrib.auth.models import User
from bulkuploads.models import BulkUpload
from apicodes.models import APICodes
from products.models import Product
from products.models import ProductError
from products.models import ProductErrorAggregate
from . import models
from . import forms
from products.forms import ProductForm
from bulkuploads.forms import BulkUploadForm
import csv
from employers.utils import BulkCreateManager
from employers.utils import ApiDomains
import os.path
from os import path
from django.utils.text import slugify
import misaka
import uuid
from django.shortcuts import get_object_or_404

import boto3
import requests
import json
import re
from botocore.exceptions import NoCredentialsError
import io
from django.db.models import Count

from events.forms import EventForm
from events.models import Event


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
            form.instance.record_status = "Created"
            form.instance.source = "Web App"

            return super().form_valid(form)


#Pull from  backend system of record(SOR)
@permission_required("products.add_product")
@login_required
def BackendPull(request, pk):
        # fetch the object related to passed id
        #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI/latest'

        prod_obj = get_object_or_404(Product, pk = pk)

        api = ApiDomains()
        url = api.product + "/" + "latest"
        payload={'ident': prod_obj.productid}
        resp = requests.get(url, params=payload)
        print(resp.text)
        print(resp.status_code)
        obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
        status_message=obj.http_response_message
        mesg=str(resp.status_code) + " - " + status_message
        if resp.status_code != 200:
            # This means something went wrong.
            #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
            #raise APIError(resp.status_code)
            message={'messages':mesg}
            return render(request, "messages.html", context=message)
        else:
            json_data = json.loads(resp.text)

            # fetch the object related to passed id
            #obj = get_object_or_404(Product, pk = json_data["LOCAL_ID"])

            # pass the object as instance in form
            #form = ProductForm(request.POST or None, instance = obj)

            #OVERRIDE THE OBJECT WITH API data
            obj.pk = int(json_data["LOCAL_ID"])
            obj.productid = json_data["PRODUCT_ID"]
            obj.name = json_data["NAME"]
            obj.type = json_data["TYPE"]
            obj.coverage_limit = json_data["COVERAGE_LIMIT"]
            obj.price_per_1000_units = json_data["RATE"]
            obj.product_date = json_data["CREATE_DATE"]
            obj.description = json_data["DESCRIPTION"]
            obj.description_html = misaka.html(obj.description)
            obj.photo = json_data["PHOTO"]
            obj.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj.create_date = json_data["CREATE_DATE"]
            obj.backend_SOR_connection = json_data["CONNECTION"]
            obj.response = json_data["RESPONSE"]
            obj.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj.record_status = json_data["RECORD_STATUS"]

            context = {'product_details':obj}

            return render(request, "products/product_detail.html", context=context)



#Pull from  backend system of record(SOR)
@permission_required("products.add_product")
@login_required
def ListProductsHistory(request, pk):

                context ={}

                prod_obj = get_object_or_404(Product, pk = pk)

                api = ApiDomains()
                url = api.product + "/" + "history"
                #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI/history'
                payload={'ident': prod_obj.productid}

                resp = requests.get(url, params=payload)
                print(resp.status_code)
                obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
                status_message=obj.http_response_message
                mesg=str(resp.status_code) + " - " + status_message

                if resp.status_code != 200:
                    # This means something went wrong.
                    #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
                    #raise APIError(resp.status_code)
                    message={'messages':mesg}
                    return render(request, "messages.html", context=message)
                else:
                    json_data=[]
                    dict_data=[]
                    obj_data=[]
                    json_data = resp.json()

                    #print(json_data[0])
                    #print(json_data[1])
                    for ix in range(len(json_data)):
                     obj = Product()
                      #dict_data.append(json.loads(json_data[ix]))
                     obj.pk = int(json_data[ix]["LOCAL_ID"])
                     obj.productid = json_data[ix]["PRODUCT_ID"]
                     obj.name = json_data[ix]["NAME"]
                     obj.type = json_data[ix]["TYPE"]
                     obj.coverage_limit = json_data[ix]["COVERAGE_LIMIT"]
                     obj.price_per_1000_units = json_data[ix]["RATE"]
                     obj.product_date = json_data[ix]["CREATE_DATE"]
                     obj.description = json_data[ix]["DESCRIPTION"]
                     obj.description_html = misaka.html(obj.description)
                     #obj.photo = json_data[ix]["PHOTO"]
                     obj.creator = User.objects.get(pk=int(json_data[ix]["CREATOR"]))
                     obj.create_date = json_data[ix]["CREATE_DATE"]
                     obj.backend_SOR_connection = json_data[ix]["CONNECTION"]
                     obj.response = json_data[ix]["RESPONSE"]
                     obj.record_status = json_data[ix]["RECORD_STATUS"]
                     obj.commit_indicator = json_data[ix]["COMMIT_INDICATOR"]

                     obj_data.append(obj)

                    context = {'object_list':obj_data}

                    return render(request, "products/product_list.html", context=context)

                    #mesg_obj = get_object_or_404(APICodes, http_response_code = 1000)
                    #status_message=mesg_obj.http_response_message
                    #mesg="1000" + " - " + status_message
                    # add form dictionary to context
                    #message={'messages':mesg}
                    #return render(request, "messages.html", context=message)


@permission_required("products.add_product")
@login_required
def RefreshProduct(request, pk):
        # fetch the object related to passed id
        context ={}
        prod_obj = get_object_or_404(Product, pk = pk)

        api = ApiDomains()
        url = api.product + "/" + "refresh"
        #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI/history'
        payload={'ident': prod_obj.productid}

        resp = requests.get(url, params=payload)
        print(resp.status_code)

        obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
        status_message=obj.http_response_message
        mesg=str(resp.status_code) + " - " + status_message

        if resp.status_code != 200:
            # This means something went wrong.
            #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
            #raise APIError(resp.status_code)
            message={'messages':mesg}
            return render(request, "messages.html", context=message)
        else:
            json_data=[]

            json_data = resp.json()
            obj1=Product()

            #OVERRIDE THE OBJECT WITH API data
            obj1.pk = int(json_data["LOCAL_ID"])
            obj1.productid = json_data["PRODUCT_ID"]
            obj1.name = json_data["NAME"]
            obj1.type = json_data["TYPE"]
            obj1.coverage_limit = json_data["COVERAGE_LIMIT"]
            obj1.price_per_1000_units = json_data["RATE"]
            obj1.product_date = json_data["CREATE_DATE"]
            obj1.description = json_data["DESCRIPTION"]
            obj1.description_html = misaka.html(obj1.description)
            #obj1.photo = json_data["PHOTO"]
            obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
            #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
            obj1.create_date = json_data["CREATE_DATE"]
            obj1.backend_SOR_connection = "Disconnected"
            obj1.response = json_data["RESPONSE"]
            obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
            obj1.record_status = json_data["RECORD_STATUS"]

            #Log events
            event = Event()
            event.EventTypeCode = "PRR"
            event.EventSubjectId = obj1.productid
            event.EventSubjectName = obj1.name
            event.EventTypeReason = "Product refreshed from ODS"
            event.source = "Web App"
            event.creator=obj1.creator
            event.save()

            obj1.save()

            context = {'product_details':obj1}

            return render(request, "products/product_detail.html", context=context)


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
            form.instance.record_status = "Created"

            #Log events
            event = Event()
            event.EventTypeCode = "PRV"
            event.EventSubjectId = form.instance.productid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Product versioned"
            event.source = "Web App"
            event.creator=request.user
            event.save()

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
            form.instance.record_status = "Updated"

            #Log events
            event = Event()
            event.EventTypeCode = "PRU"
            event.EventSubjectId = form.instance.productid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Product updated"
            event.source = "Web App"
            event.creator=self.request.user
            event.save()

            return super().form_valid(form)


class DeleteProduct(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'products.delete_product'
    context_object_name = 'product_details'
    form_class = forms.ProductForm
    model = models.Product
    template_name = 'products/product_delete_confirm.html'
    success_url = reverse_lazy("products:all")

    def form_valid(self, form):
        print("hello")
        if not self.request.user.has_perm('products.delete_product'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user

            #Log events
            event = Event()
            event.EventTypeCode = "PRD"
            event.EventSubjectId = form.instance.productid
            event.EventSubjectName = form.instance.name
            event.EventTypeReason = "Product deleted"
            event.source = "Web App"
            event.creator=self.request.user
            event.save()

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
            Q(productid__icontains=query) | Q(name__icontains=query) | Q(type__icontains=query) | Q(description__icontains=query)
        )

        #change start for remote SearchProductsForm
        if not object_list:
            api = ApiDomains()
            url = api.product + "/" + "refresh"
            #url = 'https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI/history'
            payload={'ident': query}

            resp = requests.get(url, params=payload)
            print(resp.status_code)

            obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
            status_message=obj.http_response_message
            mesg=str(resp.status_code) + " - " + status_message

            if resp.status_code != 200:
                # This means something went wrong.
                #raise ApiError('GET /tasks/ {}'.format(resp.status_code))
                #raise APIError(resp.status_code)
                #message={'messages':mesg}
                #return render(self.request, "messages.html", context=message)
                print("Status Code: " + str(resp.status_code))
            else:
                json_data=[]

                json_data = resp.json()
                obj_data=[]
                obj1=Product()

                #OVERRIDE THE OBJECT WITH API data
                obj1.pk = int(json_data["LOCAL_ID"])
                obj1.productid = json_data["PRODUCT_ID"]
                obj1.name = json_data["NAME"]
                obj1.type = json_data["TYPE"]
                obj1.coverage_limit = json_data["COVERAGE_LIMIT"]
                obj1.price_per_1000_units = json_data["RATE"]
                obj1.product_date = json_data["CREATE_DATE"]
                obj1.description = json_data["DESCRIPTION"]
                obj1.description_html = misaka.html(obj1.description)
                #obj1.photo = json_data["PHOTO"]
                obj1.creator = User.objects.get(pk=int(json_data["CREATOR"]))
                #obj.crerator = get_object_or_404(User, pk=obj.creatorid)
                obj1.create_date = json_data["CREATE_DATE"]
                obj1.backend_SOR_connection = "Disconnected"
                obj1.response = "Pulled From Backend"
                obj1.commit_indicator = json_data["COMMIT_INDICATOR"]
                obj1.record_status = json_data["RECORD_STATUS"]

                obj1.save()



                #obj_data.append(obj1)
                #print(obj_data)

                #context = {'object_list':obj_data}

                #return render(self.request, "products/product_search_list.html", context=context)
                object_remote_list = Product.objects.filter(productid=query)
                print(object_remote_list)
                return object_remote_list

        else:
        #change end for remote SearchProductsForm

            return object_list



@permission_required("products.add_product")
@login_required
def BulkUploadProduct(request):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.client('s3')
                    s3.download_file('intellidatastatic1', 'media/products.csv', 'products.csv')

                    with open('products.csv', 'rt') as csv_file:
                        array_good =[]
                        array_bad = []
                        #array_bad =[]
                        next(csv_file) # skip header line
                        for row in csv.reader(csv_file):
                                                      bad_ind = 0
                                                      array1=[]
                                                      array2=[]

                                                      #populate serial number
                                                      serial=row[0]
                                                      array2.append(serial)

                                                    #pass product:
                                                      productid=row[1]
                                                      array2.append(productid)
                                                       #validate name
                                                      name=row[2]
                                                      if name == "":
                                                          bad_ind = 1
                                                          description = "Name is mandatory"
                                                          array1.append(serial)
                                                          array1.append(productid)
                                                          array1.append(name)
                                                          array1.append(name)
                                                          array1.append(description)
                                                          array_bad.append(array1)

                                                      else:
                                                          array2.append(name)

                                                      slug=slugify(name)
                                                      #array2.append(slug)

                                                      type=row[3]
                                                      array2.append(type)

                                                      description=row[4]
                                                      array2.append(description)

                                                      description_html = misaka.html(description)

                                                      coverage_limit=row[5]
                                                      array2.append(coverage_limit)

                                                      price_per_1000_units=row[6]
                                                      array2.append(price_per_1000_units)

                                                      if bad_ind == 0:
                                                          array_good.append(array2)



                        # create good file
                    #with open('products1.csv', 'w', newline='') as clean_file:
                    ##    writer = csv.writer(clean_file)
                    #    writer.writerows(array_good)

                    buff1 = io.StringIO()

                    writer = csv.writer(buff1, dialect='excel', delimiter=',')
                    writer.writerows(array_good)

                    buff2 = io.BytesIO(buff1.getvalue().encode())

                        # check if a version of the good file already exists
                #    try:
                #        s3.Object('my-bucket', 'dootdoot.jpg').load()
                #    except botocore.exceptions.ClientError as e:
                #        if e.response['Error']['Code'] == "404":
                #            # The object does not exist.
                #            ...
                #        else:
                #            # Something else has gone wrong.
                #            raise
                #    else:
                #        # do something

# create good file
                    try:
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/products1.csv')
                        s3.upload_fileobj(buff2, 'intellidatastatic1', 'media/products1.csv')
                        print("Good File Upload Successful")

                    except FileNotFoundError:
                         print("The good file was not found")

                    except NoCredentialsError:
                         print("Credentials not available")


                           # create bad file
                    #with open('product_error.csv', 'w', newline='') as error_file:
                    #       writer = csv.writer(error_file)
                    #       writer.writerows(array1)

                    buff3 = io.StringIO()

                    writer = csv.writer(buff3, dialect='excel', delimiter=',')
                    writer.writerows(array_bad)

                    buff4 = io.BytesIO(buff3.getvalue().encode())


                        # save bad file to S3
                    try:
                        response = s3.delete_object(Bucket='intellidatastatic1', Key='media/products_error.csv')
                        s3.upload_fileobj(buff4, 'intellidatastatic1', 'media/products_error.csv')
                        print("Bad File Upload Successful")

                    except FileNotFoundError:
                        print("The bad file was not found")

                    except NoCredentialsError:
                        print("Credentials not available")

                    # load the product table
                    s3.download_file('intellidatastatic1', 'media/products1.csv', 'products1.csv')

                    with open('products1.csv', 'rt') as csv_file:
                        bulk_mgr = BulkCreateManager(chunk_size=20)

                        for row in csv.reader(csv_file):
                            if row[1] == "":
                                bulk_mgr.add(models.Product(productid = str(uuid.uuid4())[26:36],
                                                          name=row[2],
                                                          slug=slugify(row[2]),
                                                          type=row[3],
                                                          description=row[4],
                                                          description_html = misaka.html(row[4]),
                                                          coverage_limit=row[5],
                                                          price_per_1000_units=row[6],
                                                          creator = request.user,
                                                          source="Web App Bulk Upload",
                                                          record_status = "Created",
                                                          bulk_upload_indicator = "Y"
                                                          ))
                            else:
                                bulk_mgr.add(models.Product(productid = row[1],
                                                           name=row[2],
                                                           slug=slugify(row[2]),
                                                           type=row[3],
                                                           description=row[4],
                                                           description_html = misaka.html(row[4]),
                                                           coverage_limit=row[5],
                                                           price_per_1000_units=row[6],
                                                           creator = request.user,
                                                           source="Web App Bulk Upload",
                                                           record_status = "Created",
                                                           bulk_upload_indicator = "Y"

                                                          ))

                        bulk_mgr.done()

                        # load the product error table
                        s3.download_file('intellidatastatic1', 'media/products_error.csv', 'products_error.csv')

                        #Refresh Error table for concerned employer
                        ProductError.objects.all().delete()

                        with open('products_error.csv', 'rt') as csv_file:
                            bulk_mgr = BulkCreateManager(chunk_size=20)
                            for row1 in csv.reader(csv_file):
                                bulk_mgr.add(models.ProductError(serial = row1[0],
                                                          productid=row1[1],
                                                          name=row1[2],
                                                          errorfield=row1[3],
                                                          error_description=row1[4],
                                                          creator = request.user,
                                                          source="Web App Bulk Upload"
                                                          ))
                            bulk_mgr.done()


                    error_report = ProductErrorAggregate()

                    error_report.clean=Product.objects.count()
                    error_report.error=ProductError.objects.count()

                    error_report.total=(error_report.clean + error_report.error)

                    #Refresh Error aggregate table for concerned employer
                    ProductErrorAggregate.objects.all().delete()

                    error_report.save()

                    #Log events
                    event = Event()
                    event.EventTypeCode = "PRB"
                    event.EventSubjectId = "bulkproducts"
                    event.EventSubjectName = "Bulk processing"
                    event.EventTypeReason = "Products uploaded in bulk"
                    event.source = "Web App"
                    event.creator=request.user
                    event.save()



                    return HttpResponseRedirect(reverse("products:all"))



                    #return HttpResponseRedirect(reverse("products:all"))

        else:
                            # add form dictionary to context
                    context["form"] = form

                    return render(request, "bulkuploads/bulkupload_form.html", context)


@permission_required("products.add_product")
@login_required
def BulkUploadProduct_deprecated(request):

    context ={}

    form = BulkUploadForm(request.POST, request.FILES)

    if form.is_valid():
                form.instance.creator = request.user
                form.save()

                s3 = boto3.client('s3')
                s3.download_file('intellidatastatic1', 'media/products.csv', 'products.csv')

                #with open('/tmp/{"products.csv"}', 'rt') as csv_file:
                with open('products.csv', 'rt') as csv_file:
                    bulk_mgr = BulkCreateManager(chunk_size=20)
                    for row in csv.reader(csv_file):
                        bulk_mgr.add(models.Product(

                                                  productid = str(uuid.uuid4())[26:36],
                                                  name=row[0],
                                                  slug=slugify(row[0]),
                                                  type=row[1],
                                                  description=row[2],
                                                  description_html = misaka.html(row[2]),
                                                  coverage_limit=row[3],
                                                  price_per_1000_units=row[4],
                                                  creator = request.user,
                                                  record_status = "Created",
                                                  bulk_upload_indicator = "Y"
                                                  ))
                    bulk_mgr.done()

                return HttpResponseRedirect(reverse("products:all"))
    else:
            # add form dictionary to context
            context["form"] = form

            return render(request, "bulkuploads/bulkupload_form.html", context)


@permission_required("products.add_product")
@login_required
def BulkUploadSOR(request):

    array = Product.objects.filter(bulk_upload_indicator='Y')
    serializer = ProductSerializer(array, many=True)
    json_array = serializer.data

    api = ApiDomains()
    url = api.product + "/" + "upload"
    #url='https://94q78vev60.execute-api.us-east-1.amazonaws.com/Prod/intellidataProductAPI'
    #post data to the API for backend connection
    resp = requests.post(url, json=json_array)
    print("status code " + str(resp.status_code))

    if resp.status_code == 502:
        resp.status_code = 201

    obj = get_object_or_404(APICodes, http_response_code = resp.status_code)
    status_message=obj.http_response_message
    mesg=str(resp.status_code) + " - " + status_message

    if resp.status_code != 201:
        # This means something went wrong.
        message={'messages':mesg}
        return render(request, "messages.html", context=message)
    else:
        Product.objects.filter(bulk_upload_indicator='Y').update(bulk_upload_indicator=" ")

        #Log events
        event = Event()
        event.EventTypeCode = "PRO"
        event.EventSubjectId = "productodsupload"
        event.EventSubjectName = "Bulk upload to ODS"
        event.EventTypeReason = "Products uploaded to ODS in bulk"
        event.source = "Web App"
        event.creator=request.user
        event.save()

        return HttpResponseRedirect(reverse("products:all"))


class ViewProductErrorList(LoginRequiredMixin, generic.ListView):
    context_object_name = 'product_error_list'
    model = models.ProductError
    template_name = 'products/product_error_list.html'

    #form_class = forms.MemberForm

    def get_queryset(self):
    #    return Member.objects.filter(employer=employer_name)
    #    return Member.objects.all
        #return models.Member.objects.prefetch_related('employer')
        return models.ProductError.objects.all()


@api_view(['GET', 'POST'])
def ProductList(request):

    if request.method == 'GET':
        contacts = Product.objects.all()
        serializer = ProductSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        product = Product()
        event = Event()

        if serializer.data["productid"] == '':
            product.productid = str(uuid.uuid4())[26:36]
            event.EventTypeReason = "New product received via API"
        else:
            product.productid = serializer.data["productid"]
            event.EventTypeReason = "Product added via API"

        product.name = serializer.data["name"]
        product.slug=slugify(product.name),

        product.description = serializer.data["description"]
        product.description_html = misaka.html(product.description),
        product.coverage_limit = serializer.data["coverage_limit"]
        product.price_per_1000_units = serializer.data["price_per_1000_units"]

        product.source = "API Call"

        product.creator = get_object_or_404(User, pk=serializer.data["creator"])

        product.backend_SOR_connection = "Disconnected"
        product.response = ""
        product.commit_indicator = "Not Committed"
        product.record_status = ""

        #Log events
        event.EventTypeCode = "PRW"
        event.EventSubjectId = product.productid
        event.EventSubjectName = product.name
        event.source = "API Call"
        event.creator=product.creator
        event.save()

        product.save()
        return Response(serializer.data)

    #if serializer.is_valid():
   #        serializer.save()

    #    return Response(serializer.data, status=status.HTTP_201_CREATED)
 #
    #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#class for handling built-in API errors
class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)
