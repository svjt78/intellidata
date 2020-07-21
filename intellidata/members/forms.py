from django import forms
from django.core.exceptions import ValidationError
from members.models import *

from .models import Member
from phonenumber_field.formfields import PhoneNumberField


class MemberForm(forms.ModelForm):
    age: forms.IntegerField()
    phone = PhoneNumberField()
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
        exclude = ('slug','creator')
        #fields = ('name', 'age')
        #fields = '__all__'
        widgets = {
            'memberid': forms.TextInput(attrs={'readonly':'readonly'}),
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'email_address': forms.EmailField(max_length = 200),
            'creator': forms.TextInput(attrs={'readonly':'readonly'}),
            'sms': forms.TextInput(attrs={'readonly':'readonly'}),
            'emailer': forms.TextInput(attrs={'readonly':'readonly'}),

        }
