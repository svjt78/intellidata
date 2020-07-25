from django import forms
from django.core.exceptions import ValidationError
from apicodes.models import APICodes

CODE_CHOICES = (
    ('STANDARD', 'STANDARD'),
    ('CUSTOM', 'Custom')
    )


class APICodesForm(forms.ModelForm):

    class Meta:
        model = APICodes

        fields = ('http_error_category', 'http_response_code', 'http_response_message', 'API_code_type')

        widgets = {

            'http_error_category': forms.TextInput(attrs={'class': 'textinputclass'}),

            'http_response_code': forms.TextInput(attrs={'class': 'textinputclass'}),

            'http_response_message': forms.TextInput(attrs={'class': 'textinputclass'})
        }
