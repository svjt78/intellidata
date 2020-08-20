from django.contrib import admin

# Register your models here.
from django.contrib import admin

from . import models


admin.site.register(models.Transmission)
admin.site.register(models.TransmissionError)
