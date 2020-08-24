from controlcenter import Dashboard, widgets
from django.db import connection
from django.db.models import Sum
from django.db.models import Count
from employers.models import Employer
from employers.models import EmployerErrorAggregate
from agreements.models import Agreement
from employees.models import Employee
from employees.models import EmployeeErrorAggregate
from products.models import Product
from products.models import ProductErrorAggregate
from transmissions.models import Transmission
from transmissions.models import TransmissionErrorAggregate


#

class TransmissionFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Employer
    title = 'Transmission feed error analysis'
    model = TransmissionErrorAggregate
    list_display = ('total', 'clean', 'error', 'error_date')


class ProductFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Employer
    title = 'Product feed error analysis'
    model = ProductErrorAggregate
    list_display = ('total', 'clean', 'error', 'error_date')

class EmployerFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Employer
    title = 'Employer feed error analysis by Transmission'
    model = EmployeeErrorAggregate
    list_display = ('Transmission', 'total', 'clean', 'error', 'error_date')

class EmployeeFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Employer
    title = 'Employee feed error analysis by Employer'
    model = EmployeeErrorAggregate
    list_display = ('Employer', 'total', 'clean', 'error', 'error_date')

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


class EmployeeByAge(widgets.SingleBarChart):
    # label and series
    title = 'Employee By Age'
    model = Employee
    values_list = ('name', 'age')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Employee.objects.values('name', 'age').filter()


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

class EmployeeCountByEmployer(widgets.SingleBarChart):
    # label and series
    title = 'Employees By Employer'
    model = Employer
    values_list = ('name', 'number_of_Employees')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Employer.objects.order_by('-number_of_Employees').annotate(number_of_Employees=Count('employee_set')) # annotate the queryset


class AgreementCountByEmployer(widgets.SingleBarChart):
    # label and series
    title = 'Agreements By Employer'
    model = Employer
    values_list = ('name', 'number_of_agreements')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Employer.objects.order_by('-number_of_agreements').annotate(number_of_agreements=Count('employer_set')) # annotate the queryset




    # Data source
    #queryset = Product.objects.order_by('-coverage_limit').annotate(Sum('coverage_limit'))

class EmployerProductAgreement(widgets.ItemList):
    # label and series
    title = 'Coverage limits by Agreements and Products'
    model = Agreement
    list_display = ('product', 'name', 'coverage')


class CoverageByEmployersProductsAgreement(widgets.SingleBarChart):
    # label and series
    title = 'Coverage by Products and Agreement'
    model = Agreement
    values_list = ('product', 'coverage')
    queryset = Agreement.objects.values('product').annotate(Sum('coverage')).order_by('coverage')

class EmployerList(widgets.ItemList):
    title = 'Employers by Purpose'
    model = Employer
    list_display = ('name', 'purpose', 'Employer_date')

#3
class AgreementList(widgets.ItemList):
    # This widget displays a list of agreements ordered in the Employer
    title = 'Agreements by Employer'
    model = Agreement
    list_display = ('name', 'Employer', 'agreement_date')

class MyDashboard(Dashboard):
    widgets = (
        TransmissionFeedErrorAnalysis,
        ProductFeedErrorAnalysis,
        EmployerFeedErrorAnalysis,
        EmployeeFeedErrorAnalysis,
        CoverageLimitsProducts,
        RateByProducts,
        EmployeeByAge,
        ProductPie,
        EmployeeCountByEmployer,
        AgreementCountByEmployer,
        EmployerProductAgreement,
        CoverageByEmployersProductsAgreement,
        ProductList,
        EmployerList,
        AgreementList,

    )
