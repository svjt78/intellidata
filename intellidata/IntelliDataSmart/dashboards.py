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

class EmployerFeedErrorAnalysis(widgets.ItemList):

    title = 'Employer bulk feed analysis by Transmission'
    model = EmployerErrorAggregate
    list_display = ('run_date', 'transmission', 'total_employers_till_date', 'processed_clean', 'number_of_error_occurences', 'volume_processed_in_this_run', 'execution_time_for_this_run')

class EmployeeFeedErrorAnalysis(widgets.ItemList):

    title = 'Employee bulk feed analysis by Employer'
    model = EmployeeErrorAggregate
    list_display = ('run_date', 'employer', 'total_employees_till_date', 'processed_clean', 'number_of_error_occurences', 'volume_processed_in_this_run', 'execution_time_for_this_run')

class TransmissionFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of transmissions ordered in the Employer
    title = 'Transmission bulk feed analysis'
    model = TransmissionErrorAggregate
    list_display = ('run_date', 'total', 'clean', 'error')


class ProductFeedErrorAnalysis(widgets.ItemList):
    # This widget displays a list of transmissions ordered in the Employer
    title = 'Product bulk feed analysis'
    model = ProductErrorAggregate
    list_display = ('run_date', 'total', 'clean', 'error')


class EmployeeDataByOrigin(widgets.SingleBarChart):
    # label and series
    values_list = ('source', 'count')
    # Data source
    queryset = Employee.objects.values('source').annotate(count=Count('pk')).order_by('-count')



class CoverageLimitsProducts(widgets.SingleBarChart):
    # label and series
    title = 'Coverage limits by Products'

    values_list = ('name', 'coverage_limit')
    # Data source
    #queryset = Product.objects.order_by('-coverage_limit')
    queryset = Product.objects.values('name').annotate(Sum('coverage_limit')).order_by('-coverage_limit')
    #limit_to = 3


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


    # Data source
    #queryset = Product.objects.order_by('-coverage_limit').annotate(Sum('coverage_limit'))



class EmployerList(widgets.ItemList):
    title = 'Employers by Purpose'
    model = Employer
    list_display = ('name', 'purpose', 'Employer_date')

#3


class MyDashboard(Dashboard):
    widgets = (
        EmployerFeedErrorAnalysis,
        EmployeeFeedErrorAnalysis,
        TransmissionFeedErrorAnalysis,
        ProductFeedErrorAnalysis,
        EmployeeDataByOrigin,
        CoverageLimitsProducts,
        RateByProducts,
        EmployeeByAge,
        ProductPie,
        EmployeeCountByEmployer,
        ProductList,
        EmployerList,

    )
