from django import forms
from django.core.exceptions import ValidationError
from .models import Product

PRODUCT_CHOICES = (
    ('LIFE', 'Life Insurance'),
    ('STD', 'Short Term Disability'),
    ('LTD', 'Long Term Disability'),
    ('CI', 'Critical Illness'),
    )

TRANSMISSION_CHOICES=[('Connected','Connected'),
     ('Disconnected','Disconnected')
     ]

class ProductForm(forms.ModelForm):

    productid: forms.TextInput(attrs={'readonly':'readonly'})
    price_per_1000_units: forms.DecimalField()
    coverage_limit: forms.DecimalField()
    photo = forms.ImageField()

    backend_SOR_connection = forms.ChoiceField(choices=TRANSMISSION_CHOICES, widget=forms.RadioSelect, label='If connected to ODS')
    commit_indicator = forms.CharField(required=False, label='If this member data is sync-ed up with ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    record_status = forms.CharField(required=False, label='If this member data got Created or Updated', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    response = forms.CharField(required=False, label='Connection response from/to ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = Product

        fields = ('productid', 'name', 'type', 'description', 'price_per_1000_units', 'coverage_limit', 'photo', 'backend_SOR_connection', 'record_status', 'response')

        widgets = {

            'productid': forms.TextInput(attrs={'readonly':'readonly'}),

            'name': forms.TextInput(attrs={'class': 'textinputclass'}),

            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),

            'photo': forms.ImageField(),

        }
