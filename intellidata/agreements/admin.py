from django.contrib import admin

from . import models

class AgreementAdmin(admin.ModelAdmin):


    search_fields = ['name', 'employer', 'product']

    list_filter = ['name', 'employer', 'product', 'agreement_date']

    list_display = ['pk', 'name', 'employer', 'agreement_date']

    list_editable = ['name']


admin.site.register(models.Agreement, AgreementAdmin)
