from django import forms
from django.core.exceptions import ValidationError
from employees.models import *

from .models import Employee
from .models import EmployeeError
from phonenumber_field.formfields import PhoneNumberField

TRANSMISSION_CHOICES=[('Connected','Connected'),
     ('Disconnected','Disconnected')
     ]

GENDER=[('Male','Male'),
     ('Female','Female'),
     ('Others','Others')
     ]

MARITAL_STATUS=[('Married','Married'),
     ('Unmarried','Unmarried')
     ]

ENROLLMENT_METHOD=[('OneOnOne','OneOnOne'),
     ('CallCenter','CallCenter'),
     ('InternetOrSelfService','InternetOrSelfService'),
     ('HumanResources','HumanResources'),
     ('Paper','Paper'),
     ('Mobile','Mobile'),
     ]

class EmployeeForm(forms.ModelForm):
    age: forms.IntegerField()
    home_phone = PhoneNumberField(required=False)
    work_phone = PhoneNumberField(required=False)
    mobile_phone = PhoneNumberField()
    ssn = forms.CharField(required=False, label='SSN', widget=forms.TextInput())
    backend_SOR_connection = forms.ChoiceField(choices=TRANSMISSION_CHOICES, widget=forms.RadioSelect, label='If connected to ODS')
    gendercode = forms.ChoiceField(choices=GENDER, widget=forms.RadioSelect, label='Gender')
    maritalstatus = forms.ChoiceField(choices=MARITAL_STATUS, widget=forms.RadioSelect, label='Marital Status')
    enrollment_method = forms.ChoiceField(choices=ENROLLMENT_METHOD, widget=forms.RadioSelect, label='Enrollment Method')
    birthdate = forms.DateField(required=False)
    sms = forms.CharField(required=False, label='SMS Notification', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    emailer = forms.CharField(required=False, label='Email Notification', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    artefact = forms.FileField(required=False)
    commit_indicator = forms.CharField(required=False, label='If this employee data is sync-ed up with ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    record_status = forms.CharField(required=False, label='If this employee data got Created or Updated', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    response = forms.CharField(required=False, label='Connection response from/to ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    # this function will be used for the validation
    def clean(self):

                # data from the form is fetched using super function
                super(EmployeeForm, self).clean()

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
        model = Employee
        exclude = ('slug','creator', 'bulk_upload_indicator')
        #fields = ('name', 'age')
        #fields = '__all__'
        widgets = {
            'employeeid': forms.TextInput(attrs={'readonly':'readonly'}),
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'email_address': forms.EmailField(max_length = 200),
            'alternate_email_address': forms.EmailField(max_length = 200),
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
        }

class EmployeeErrorForm(forms.ModelForm):

    serial = forms.CharField(required=False, label='Serial#', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    name = forms.CharField(required=False, label='Employee Name', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    errorfield = forms.CharField(required=False, label='Field At Error', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    description = forms.CharField(required=False, label='Error description_html', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    employer = forms.CharField(required=False, label='Employer', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    employerid = forms.CharField(required=False, label='Employer ID', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    #error_date = forms.DateTimeField(required=False, label='Feed Date', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = EmployeeError

        #fields = ('serial', 'name', 'errorfield', 'description', 'group', 'error_date')
        exclude = ()

        widgets = {
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
        }
