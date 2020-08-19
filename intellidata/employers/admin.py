from django.contrib import admin

# Register your models here.
from . import models


admin.site.register(models.Employer)
admin.site.register(models.EmployerError)
admin.site.register(models.EmployerErrorAggregate)
