from django.contrib import messages
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required
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
from groups.models import Group
from members.models import Member
from . import models
from . import forms
from members.forms import MemberForm
from bulkuploads.models import BulkUpload
from bulkuploads.forms import BulkUploadForm
import boto3
from botocore.exceptions import ClientError
import json
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
from members.serializers import MemberSerializer


class SingleMember(LoginRequiredMixin, generic.DetailView):
    context_object_name = 'member_details'
    model = models.Member
    template_name = 'members/member_detail.html'
    #form_class = forms.MemberForm

class ListMembers(LoginRequiredMixin, generic.ListView):
    context_object_name = 'member_list'
    model = models.Member
    template_name = 'members/member_list.html'

    #form_class = forms.MemberForm

    def get_queryset(self):
    #    return Member.objects.filter(group=group_name)
    #    return Member.objects.all
        return models.Member.objects.prefetch_related('group')


class CreateMember(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    #fields = ("name", "age")
    permission_required = 'members.add_member'
    template_name = 'members/member_form.html'
    context_object_name = 'member_details'
    redirect_field_name = 'members/member_detail.html'
    model = models.Member
    form_class = forms.MemberForm

    def dispatch(self, request, *args, **kwargs):
        """
        Overridden so we can make sure the `Group` instance exists
        before going any further.
        """
        self.group = get_object_or_404(models.Group, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        if not self.request.user.has_perm('members.add_member'):
            raise HttpResponseForbidden()
        else:
            """
            Overridden to add the group relation to the `Member` instance.
            """
            form.instance.group = self.group
            form.instance.creator = self.request.user
            return super().form_valid(form)


@login_required
@permission_required("members.add_member")
def VersionMember(request, pk):
    # dictionary for initial data with
    # field names as keys
    context ={}

    # fetch the object related to passed id
    obj = get_object_or_404(Member, pk = pk)

    # pass the object as instance in form
    form = MemberForm(request.POST or None, instance = obj)

    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
            obj.pk = int(round(time.time() * 1000))
            form.instance.creator = request.user
            form.save()
            return HttpResponseRedirect(reverse("members:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "members/member_form.html", context)


class UpdateMember(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    #fields = ("name", "age")
    permission_required = 'members.change_member'
    template_name = 'members/member_form.html'
    #context_object_name = 'member_details'
    redirect_field_name = 'members/member_detail.html'
    model = models.Member
    form_class = forms.MemberForm

    def form_valid(self, form):

        if not self.request.user.has_perm('members.change_member'):
            raise HttpResponseForbidden()
        else:
            form.instance.creator = self.request.user
            return super().form_valid(form)


class DeleteMember(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView,):
    permission_required = 'members.delete_member'
    context_object_name = 'member_details'
    form_class = forms.MemberForm
    model = models.Member
    template_name = 'members/member_delete_confirm.html'
    success_url = reverse_lazy("members:all")


    def delete(self, *args, **kwargs):
        messages.success(self.request, "Member Deleted")
        return super().delete(*args, **kwargs)

    def form_valid(self, form):

        if not self.request.user.has_perm('members.delete_member'):
            raise HttpResponseForbidden()
        else:
            return super().form_valid(form)


def SearchMembersForm(request):
    return render(request,'members/member_search_form.html')


class SearchMembersList(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    model = models.Member
    template_name = 'members/member_search_list.html'

    def get_queryset(self, **kwargs): # new
        query = self.request.GET.get('q', None)
        object_list = models.Member.objects.filter(
            Q(name__icontains=query) | Q(age__icontains=query)
        )
        return object_list


@permission_required("members.add_member")
@login_required
def BulkUploadMember(request, pk, *args, **kwargs):

        context ={}

        form = BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
                    form.instance.creator = request.user
                    form.save()

                    s3 = boto3.client('s3')
                    s3.download_file('intellidatastatic', 'media/members.csv', 'members.csv')

                    with open('members.csv', 'rt') as csv_file:
                        bulk_mgr = BulkCreateManager(chunk_size=20)
                        for row in csv.reader(csv_file):
                            bulk_mgr.add(models.Member(memberid = str(uuid.uuid4())[26:36],
                                                      name=row[0],
                                                      slug=slugify(row[0]),
                                                      age=int(row[1]),
                                                      email=row[2],
                                                      phone=row[3],
                                                      group=get_object_or_404(models.Group, pk=pk),
                                                      creator = request.user
                                                      ))
                        bulk_mgr.done()

                    return HttpResponseRedirect(reverse("members:all"))

        else:
                            # add form dictionary to context
                    context["form"] = form

                    return render(request, "bulkuploads/bulkupload_form.html", context)


#Send for subscription
@permission_required("members.add_member")
@login_required
def SubscribeMember(request, pk):

    context ={}

    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:215632354817:intellidata_notify_topic'

    obj = get_object_or_404(Member, pk = pk)

    form = MemberForm(request.POST or None, instance = obj)

    if form.is_valid():
        number = str(form["phone"]).strip()
        number_array = number.split()
        number = number_array[3]
        number=number.split("=")[1]
        #to_email_address=to_email_address.strip(")
        number=number.replace('"', '')
        print("that is what I see " + number )
        #emailaddr = str(form["email"])

        # Add  Subscribers
        try:
            response = sns.subscribe(
                        TopicArn=topic_arn,
                        Protocol='SMS',
                        Endpoint=number
                       )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Subscription done!"),
            obj.sms = "Phone Number Subscribed On " + str(datetime.date.today())
        #form.emailer = "Email Notification Sent on " + str(datetime.date.today())
        form.save()
        return HttpResponseRedirect(reverse("members:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "members/member_form.html", context)



@permission_required("members.add_member")
@login_required
def TextMember(request, pk):

    context = {}

    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:215632354817:intellidata_notify_topic'

    message = "Start Enrollment using http://www.google.com"
    messageJSON = json.dumps({"message":message})

    obj = get_object_or_404(Member, pk = pk)

    form = MemberForm(request.POST or None, instance = obj)

    if form.is_valid():

        try:
            response=sns.publish(
                        TopicArn=topic_arn,
                        Message=message
                     )

        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("SMS sent!"),
            obj.sms = "SMS Notification Sent on " + str(datetime.date.today())

        form.save()
        return HttpResponseRedirect(reverse("members:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "members/member_form.html", context)



@permission_required("members.add_member")
@login_required
def EmailMember(request, pk):

    context = {}

    message = "Start Enrollment"
    messageJSON = json.dumps({"message":message})

    obj = get_object_or_404(Member, pk = pk)

    form = MemberForm(request.POST or None, instance = obj)

    if form.is_valid():
        to_email = str(form["email"]).strip()
        to_email_array = to_email.split()
        to_email_value = to_email_array[3]
        to_email_address=to_email_value.split("=")[1]
        #to_email_address=to_email_address.strip(")
        to_email_address=to_email_address.replace('"', '')
        #to_email_address = "'{}'".format(to_email_address)

        #print("what we see is " + to_email_address)
        #to_email = 'svjt78@gmail.com'
        from_email = 'suvojit.dt@gmail.com'
            # Replace sender@example.com with your "From" address.
        # This address must be verified with Amazon SES.

        SENDER = from_email

        # Replace recipient@example.com with a "To" address. If your account
        # is still in the sandbox, this address must be verified.
        RECIPIENT = to_email_address

        # Specify a configuration set. If you do not want to use a configuration
        # set, comment the following variable, and the
        # ConfigurationSetName=CONFIGURATION_SET argument below.
        #CONFIGURATION_SET = "ConfigSet"

        # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
        AWS_REGION = "us-east-1"

        # The subject line for the email.
        SUBJECT = "Enrollment"

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = ("Start Enrollment\r\n"
                     "You are being requested to start "
                     "Enrollemnt"
                    )

        # The HTML body of the email.
        BODY_HTML = """<html>
        <head></head>
        <body>
          <h1>Start Enrollment</h1>
          <p>This email was sent with
            <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
            <a href='https://aws.amazon.com/sdk-for-python/'>
              AWS SDK for Python (Boto)</a>.</p>
        </body>
        </html>
                    """

        # The character encoding for the email.
        CHARSET = "UTF-8"

        # Create a new SES resource and specify a region.
        client = boto3.client('ses',region_name=AWS_REGION)

        # Try to send the email.
        try:
            #Provide the contents of the email.
            response = client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': CHARSET,
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                #ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
            obj.emailer = "Email Notification Sent on " + str(datetime.date.today())

        #form.emailer = "Email Notification Sent on " + str(datetime.date.today())
        form.save()
        return HttpResponseRedirect(reverse("members:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "members/member_form.html", context)




#rest API call
@api_view(['GET', 'POST'])
def MemberList(request):

    if request.method == 'GET':
        contacts = Member.objects.all()
        serializer = MemberSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = MemberSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#rest API call
@api_view(['GET', 'POST'])
def MemberListByGroup(request, pk):

    if request.method == 'GET':
        contacts = Member.objects.filter(group_id = pk)
        serializer = MemberSerializer(contacts, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = MemberSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




#notify members in email and text message on phone

#publish message

@permission_required("members.add_member")
@login_required
def NotifyMember_deprecated(request, pk):

    context = {}

    sns = boto3.client('sns')

    topic_arn = 'arn:aws:sns:us-east-1:215632354817:intellidata_notify_topic'

    message = "Start Enrollment"
    messageJSON = json.dumps({"message":message})

    obj = get_object_or_404(Member, pk = pk)

    form = MemberForm(request.POST or None, instance = obj)

    if form.is_valid():
        number = str(form["phone"])
        email = str(form["email"])

        sns.subscribe(
                TopicArn=topic_arn,
                Protocol='Email-JSON',
                Endpoint="svjt78@gmail.com"
        )

        sns.publish(
            TopicArn=topic_arn,
            Message=messageJSON
        )

    #number = '+17702233322'
    #sns.publish(PhoneNumber = number, Message='example text message' )

    # Add SMS Subscribers


        form["sms"] = "SMS Notification Sent on " + str(datetime.date.today())
        form["emailer"] = "Email Notification Sent on " + str(datetime.date.today())
        form.save()
        return HttpResponseRedirect(reverse("members:all"))

    else:

            # add form dictionary to context
            context["form"] = form

            return render(request, "members/member_form.html", context)
