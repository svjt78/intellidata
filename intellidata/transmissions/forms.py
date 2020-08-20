from django import forms
from django.core.exceptions import ValidationError
from .models import Transmission
from .models import TransmissionError


TRANSMISSION_CHOICES=[('Connected','Connected'),
     ('Disconnected','Disconnected')
     ]

class TransmissionForm(forms.ModelForm):

    transmissionid: forms.TextInput(attrs={'readonly':'readonly'})

    transmissionid: forms.TextInput(attrs={'readonly':'readonly'})
    price_per_1000_units: forms.DecimalField()
    coverage_limit: forms.DecimalField()

    backend_SOR_connection = forms.ChoiceField(choices=TRANSMISSION_CHOICES, widget=forms.RadioSelect, label='If connected to ODS')
    commit_indicator = forms.CharField(required=False, label='If this transmission data is sync-ed up with ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    record_status = forms.CharField(required=False, label='If this transmission data got Created or Updated', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    response = forms.CharField(required=False, label='Connection response from/to ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = Transmission

        exclude = ('creator', 'bulk_upload_indicator')

        widgets = {

            'transmissionid': forms.TextInput(attrs={'readonly':'readonly'}),

            'SenderName': forms.TextInput(attrs={'class': 'textinputclass'}),

            'BenefitAdministratorPlatform': forms.TextInput(attrs={'class': 'textinputclass'}),

            'ReceiverName': forms.TextInput(attrs={'class': 'textinputclass'}),

            'TestProductionCode': forms.TextInput(attrs={'class': 'textinputclass'}),

            'TransmissionTypeCode': forms.TextInput(attrs={'class': 'textinputclass'}),

            'SystemVersionIdentifier': forms.TextInput(attrs={'class': 'textinputclass'}),

        }

class TransmissionErrorForm(forms.ModelForm):

    serial = forms.CharField(required=False, label='Serial#', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    name = forms.CharField(required=False, label='Transmission Name', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    errorfield = forms.CharField(required=False, label='Field At Error', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    error_description = forms.CharField(required=False, label='Error description_html', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    #error_date = forms.DateTimeField(required=False, label='Feed Date', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = TransmissionError

        #fields = ('serial', 'name', 'errorfield', 'description', 'group', 'error_date')
        exclude = ()

        widgets = {
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
        }
