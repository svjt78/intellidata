from django import forms

from .models import Group


class GroupForm(forms.ModelForm):

    photo = forms.ImageField()

    class Meta:
        model = Group
        fields = ('groupid', 'name','description', 'purpose', 'photo')

        widgets = {
            'groupid': forms.TextInput(attrs={'readonly':'readonly'}),
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),
            'purpose': forms.TextInput(attrs={'class': 'textinputclass'}),
            'photo': forms.ImageField()

        }
