from django import forms
from django.core.exceptions import ValidationError
from emails.models import Email

CODE_CHOICES = (
    ('PLANADMIN', 'Plan Admin'),
    ('ADMINISTRATOR', 'Administrator')
    )


class EmailForm(forms.ModelForm):

    class Meta:
        model = Email

        fields = ('employer', 'role', 'emailaddress')

        widgets = {

            'email_address': forms.EmailField(max_length = 200),

            'operator': forms.TextInput(attrs={'readonly':'readonly'}),

        }
