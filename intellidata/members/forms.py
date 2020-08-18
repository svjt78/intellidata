from django import forms
from django.core.exceptions import ValidationError
from members.models import *

from .models import Member
from .models import MemberError
from phonenumber_field.formfields import PhoneNumberField

TRANSMISSION_CHOICES=[('Connected','Connected'),
     ('Disconnected','Disconnected')
     ]

class MemberForm(forms.ModelForm):
    age: forms.IntegerField()
    phone = PhoneNumberField()
    backend_SOR_connection = forms.ChoiceField(choices=TRANSMISSION_CHOICES, widget=forms.RadioSelect, label='If connected to ODS')
    sms = forms.CharField(required=False, label='SMS Notification', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    emailer = forms.CharField(required=False, label='Email Notification', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    artefact = forms.FileField(required=False)
    commit_indicator = forms.CharField(required=False, label='If this member data is sync-ed up with ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    record_status = forms.CharField(required=False, label='If this member data got Created or Updated', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    response = forms.CharField(required=False, label='Connection response from/to ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    # this function will be used for the validation
    def clean(self):

                # data from the form is fetched using super function
                super(MemberForm, self).clean()

                # extract the username and text field from the data
                phone = self.cleaned_data.get('phone')
                age = self.cleaned_data.get('age')

                # age range check
                if (age <= 0 or age >= 100):
                    self._errors['age'] = self.error_class([
                        'Age is valid only in range of 1 and 99'])

                # return any errors if found
                return self.cleaned_data


    class Meta:
        model = Member
        exclude = ('slug','creator', 'bulk_upload_indicator')
        #fields = ('name', 'age')
        #fields = '__all__'
        widgets = {
            'memberid': forms.TextInput(attrs={'readonly':'readonly'}),
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'email_address': forms.EmailField(max_length = 200),
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
        }

class MemberErrorForm(forms.ModelForm):

    serial = forms.CharField(required=False, label='Serial#', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    name = forms.CharField(required=False, label='Member Name', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    errorfield = forms.CharField(required=False, label='Field At Error', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    description = forms.CharField(required=False, label='Error description_html', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    group = forms.CharField(required=False, label='Group', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    #error_date = forms.DateTimeField(required=False, label='Feed Date', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = MemberError

        #fields = ('serial', 'name', 'errorfield', 'description', 'group', 'error_date')
        exclude = ()

        widgets = {
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
        }
