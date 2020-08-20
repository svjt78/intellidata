from django import forms
from django.core.exceptions import ValidationError
from employees.models import *

from .models import Agreement


class AgreementForm(forms.ModelForm):
    price_per_1000_units: forms.DecimalField()
    coverage: forms.DecimalField()

    class Meta:
        model = Agreement
        exclude = ('slug',)

        fields = ('agreementid', 'name','description', 'employer', 'product', 'price_per_1000_units', 'coverage',)

        widgets = {
            'agreementid': forms.TextInput(attrs={'readonly':'readonly'}),
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),

        }
