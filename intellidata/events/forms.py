from django import forms
from django.core.exceptions import ValidationError
from .models import Event

TRANSMISSION_CHOICES=[('Connected','Connected'),
     ('Disconnected','Disconnected')
     ]

class EventForm(forms.ModelForm):

    eventid = commit_indicator = forms.CharField(required=False, label='Event ID', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    EventTypeCode = forms.CharField(required=False, label='Event Type Code', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    EventTypeReason = forms.CharField(required=False, label='Event Type Reason', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    backend_SOR_connection = forms.ChoiceField(choices=TRANSMISSION_CHOICES, widget=forms.RadioSelect, label='If connected to ODS')
    commit_indicator = forms.CharField(required=False, label='If this event data is sync-ed up with ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    record_status = forms.CharField(required=False, label='If this event data got Created or Updated', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    response = forms.CharField(required=False, label='Connection response from/to ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = Event

        exclude = ('bulk_upload_indicator',)

        widgets = {



        }
