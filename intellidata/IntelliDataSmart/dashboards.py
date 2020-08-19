from controlcenter import Dashboard, widgets
from django.db import connection
from django.db.models import Sum
from django.db.models import Count
from products.models import Product
from groups.models import Group
from agreements.models import Agreement
from members.models import Member
from members.models import MemberErrorAggregate
from products.models import ProductErrorAggregate

#

class MemberFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Group
    title = 'Member feed error analysis by Group'
    model = MemberErrorAggregate
    list_display = ('group', 'total', 'clean', 'error', 'error_date')

class ProductFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Group
    title = 'Product feed error analysis'
    model = ProductErrorAggregate
    list_display = ('total', 'clean', 'error', 'error_date')

class CoverageLimitsProducts(widgets.SingleBarChart):
    # label and series
    title = 'Coverage limits by Products'

    values_list = ('name', 'coverage_limit')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Product.objects.values('name').annotate(Sum('coverage_limit')).order_by('-coverage_limit')
    #limit_to = 3


class CoverageLimitsAgreements(widgets.SingleBarChart):
    # label and series
    title = 'Coverage limits by Agreements'

    values_list = ('agreements_products_set', 'coverage_limit')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Product.objects.values('name').annotate(Sum('coverage_limit')).order_by('agreements_products_set')


class RateByProducts(widgets.SingleBarChart):
    # label and series
    title = 'Rate by Products'

    values_list = ('name', 'price_per_1000_units')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Product.objects.values('name', 'price_per_1000_units').filter()


class MemberByAge(widgets.SingleBarChart):
    # label and series
    title = 'Member By Age'
    model = Member
    values_list = ('name', 'age')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Member.objects.values('name', 'age').filter()


class ProductPie(widgets.SinglePieChart):
    # label and series
    values_list = ('type', 'count')
    # Data source
    queryset = Product.objects.values('type').annotate(count=Count('pk')).order_by('-count')
    limit_to = 10

class ProductList(widgets.ItemList):
    # label and series
    list_display = ('type', 'count')
    # Data source
    queryset = Product.objects.values('type').annotate(count=Count('pk')).order_by('-count')
    limit_to = 10

class MemberCountByGroup(widgets.SingleBarChart):
    # label and series
    title = 'Members By Group'
    model = Group
    values_list = ('name', 'number_of_members')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Group.objects.order_by('-number_of_members').annotate(number_of_members=Count('member_set')) # annotate the queryset


class AgreementCountByGroup(widgets.SingleBarChart):
    # label and series
    title = 'Agreements By Group'
    model = Group
    values_list = ('name', 'number_of_agreements')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Group.objects.order_by('-number_of_agreements').annotate(number_of_agreements=Count('group_set')) # annotate the queryset




    # Data source
    #queryset = Product.objects.order_by('-coverage_limit').annotate(Sum('coverage_limit'))

class GroupProductAgreement(widgets.ItemList):
    # label and series
    title = 'Coverage limits by Agreements and Products'
    model = Agreement
    list_display = ('product', 'name', 'coverage')


class CoverageByGroupsProductsAgreement(widgets.SingleBarChart):
    # label and series
    title = 'Coverage by Products and Agreement'
    model = Agreement
    values_list = ('product', 'coverage')
    queryset = Agreement.objects.values('product').annotate(Sum('coverage')).order_by('coverage')

class GroupList(widgets.ItemList):
    title = 'Groups by Purpose'
    model = Group
    list_display = ('name', 'purpose', 'group_date')

#3
class AgreementList(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Group
    title = 'Agreements by Group'
    model = Agreement
    list_display = ('name', 'group', 'agreement_date')

class MyDashboard(Dashboard):
    widgets = (
        MemberFeedErrorAnalysis,
        ProductFeedErrorAnalysis,
        CoverageLimitsProducts,
        RateByProducts,
        MemberByAge,
        ProductPie,
        MemberCountByGroup,
        AgreementCountByGroup,
        GroupProductAgreement,
        CoverageByGroupsProductsAgreement,
        ProductList,
        GroupList,
        AgreementList,

    )
