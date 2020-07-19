import datetime
from django.db.models import Count
from django.utils import timezone
from controlcenter import Dashboard, widgets
from django.db.models import Sum
from products.models import Product
from groups.models import Group
from agreements.models import Agreement

class MySingleBarChart(widgets.SingleBarChart):
        # label and series
        values_list = ('name', 'agreement_date')
        # Data source
        #queryset = Product.objects.order_by('-coverage_limit')
        queryset = Agreement.objects.select_related('group').filter()

        #limit_to = 3


class MyDashboard(Dashboard):
    widgets = (
        MySingleBarChart,
    )
