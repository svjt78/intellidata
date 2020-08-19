from django.contrib import admin

from . import models


admin.site.register(models.Product)
admin.site.register(models.ProductError)
admin.site.register(models.ProductErrorAggregate)
