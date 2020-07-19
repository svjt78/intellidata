from django import forms
from django.core.exceptions import ValidationError
from .models import BulkUpload

class BulkUploadForm(forms.ModelForm):

    file = forms.FileField()

    class Meta:
        model = BulkUpload

        fields = ('file', 'description', )

        widgets = {

            'file': forms.FileField(),

            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),




        }
