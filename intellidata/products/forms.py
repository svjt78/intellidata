from django import forms
from django.core.exceptions import ValidationError
from .models import Product
from .models import ProductError

PRODUCT_CHOICES = (
    ('LIFE', 'Life Insurance'),
    ('STD', 'Short Term Disability'),
    ('LTD', 'Long Term Disability'),
    ('CI', 'Critical Illness'),
    ('ACCIDENT', 'Accident'),
    ('ADND', 'Accidental Death & Dismemberment'),
    ('CANCER', 'Cancer'),
    ('DENTAL', 'DENTAL'),
    ('VISION', 'Vision'),
    ('HOSPITAL', 'Hospital'),
    ('IDI', 'Individual Disability'),
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
    commit_indicator = forms.CharField(required=False, label='If this product data is sync-ed up with ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    record_status = forms.CharField(required=False, label='If this product data got Created or Updated', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    response = forms.CharField(required=False, label='Connection response from/to ODS', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = Product

        fields = ('productid', 'name', 'type', 'description', 'price_per_1000_units', 'coverage_limit', 'photo', 'backend_SOR_connection', 'record_status', 'response')

        widgets = {

            'productid': forms.TextInput(attrs={'readonly':'readonly'}),

            'name': forms.TextInput(attrs={'class': 'textinputclass'}),

            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),

            'photo': forms.ImageField(),

        }

class ProductErrorForm(forms.ModelForm):

    serial = forms.CharField(required=False, label='Serial#', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    name = forms.CharField(required=False, label='Product Name', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    errorfield = forms.CharField(required=False, label='Field At Error', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    error_description = forms.CharField(required=False, label='Error description_html', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    source = forms.CharField(required=False, label='Origin', widget=forms.TextInput(attrs={'readonly':'readonly'}))
    #error_date = forms.DateTimeField(required=False, label='Feed Date', widget=forms.TextInput(attrs={'readonly':'readonly'}))

    class Meta:
        model = ProductError

        #fields = ('serial', 'name', 'errorfield', 'description', 'group', 'error_date')
        exclude = ()

        widgets = {
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
        }
