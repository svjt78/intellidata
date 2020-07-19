from django.contrib import admin

from . import models

class AgreementAdmin(admin.ModelAdmin):


    search_fields = ['name', 'group', 'product']

    list_filter = ['name', 'group', 'product', 'agreement_date']

    list_display = ['pk', 'name', 'group', 'agreement_date']

    list_editable = ['name']


admin.site.register(models.Agreement, AgreementAdmin)
