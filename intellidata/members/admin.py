from django.contrib import admin

# Register your models here.

from django.contrib import admin

from . import models


admin.site.register(models.Member)
admin.site.register(models.MemberError)
admin.site.register(models.MemberErrorAggregate)
