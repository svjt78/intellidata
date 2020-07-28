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

    productid: forms.IntegerField()
    price_per_1000_units: forms.DecimalField()
    coverage_limit: forms.DecimalField()
    photo = forms.ImageField()
    backend_SOR_connection = forms.ChoiceField(choices=TRANSMISSION_CHOICES, widget=forms.RadioSelect, label='Backend SOR Connection')

    class Meta:
        model = Product

        fields = ('productid', 'name', 'type', 'description', 'price_per_1000_units', 'coverage_limit', 'photo', 'backend_SOR_connection', 'transaction_status')

        widgets = {

            'name': forms.TextInput(attrs={'class': 'textinputclass'}),

            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),

            'photo': forms.ImageField(),

            'transaction_status': forms.TextInput(attrs={'readonly':'readonly'}),

            'commit_indicator': forms.TextInput(attrs={'readonly':'readonly'})

        }
