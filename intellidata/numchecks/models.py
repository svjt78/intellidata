from django.conf import settings
from datetime import datetime
from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.shortcuts import get_object_or_404, render
import requests

# https://docs.djangoproject.com/en/1.11/howto/custom-template-tags/#inclusion-tags
# This is for the in_group_members check template tag
from django import template
register = template.Library()


class Numcheck(models.Model):

#Data elements
    employee_ssn='employee_ssn'
    employee_name = 'employee_name'
    employee_gendercode = 'employee_gendercode'
    employee_age = 'employee_age'
    employee_birthdate = 'employee_birthdate'
    employee_maritalstatus =  'employee_maritalstatus'
    employee_home_address_line_1 = 'employee_home_address_line_1'
    employee_home_address_line_2 = 'employee_home_address_line_2'
    employee_home_city = 'employee_home_city'
    employee_home_state = 'employee_home_state'
    employee_home_zipcode = 'employee_home_zipcode'
    employee_mail_address_line_1 = 'employee_mail_address_line_1'
    employee_mail_address_line_2 = 'employee_mail_address_line_2'
    employee_mail_city = 'employee_mail_city'
    employee_mail_state = 'employee_mail_state'
    employee_mail_zipcode = 'employee_mail_zipcode'
    employee_work_address_line_1 = 'employee_work_address_line_1'
    employee_work_address_line_2 = 'employee_work_address_line_2'
    employee_work_city = 'employee_work_city'
    employee_work_state = 'employee_work_state'
    employee_work_zipcode = 'employee_work_zipcode'
    employee_email = 'employee_email'
    employee_alternate_email = 'employee_alternate_email'
    employee_home_phone = 'employee_home_phone'
    employee_work_phone = 'employee_work_phone'
    employee_mobile_phone = 'employee_mobile_phone'
    employee_enrollment_method = 'employee_enrollment_method'
    employee_employment_information = 'employee_employment_information'
    employer_name = 'name'
    employer_description = 'employer_description'
    employer_FederalEmployerIdentificationNumber='employer_FederalEmployerIdentificationNumber'
    employer_CarrierMasterAgreementNumber='employer_CarrierMasterAgreementNumber'
    employer_address_line_1 = 'employer_address_line_1'
    employer_address_line_2 = 'employer_address_line_2'
    employer_city = 'employer_city'
    employer_state = 'employer_state'
    employer_zipcode = 'employer_zipcode'
    employer_purpose = 'employer_purpose'
    employer_planadmin_email = 'employer_planadmin_email'
    product_name = 'product_name'
    product_type = 'product_type'
    product_description = 'product_description'
    product_coverage_limit = 'product_coverage_limit'
    product_price_per_1000_units = 'product_price_per_1000_units'
    transmission_SenderName = 'transmission_SenderName'
    transmission_BenefitAdministratorPlatform = 'transmission_BenefitAdministratorPlatform'
    transmission_ReceiverName = 'transmission_ReceiverName'
    transmission_TestProductionCode = 'transmission_TestProductionCode'
    transmission_TransmissionTypeCode = 'transmission_TransmissionTypeCode'
    transmission_SystemVersionIdentifier = 'transmission_SystemVersionIdentifier'
    transmission_planadmin_email = 'transmission_planadmin_email'

    CHOICES = (

        (employee_ssn, 'employee_ssn'),
        (employee_name, 'employee_name'),
        (employee_gendercode, 'employee_gendercode'),
        (employee_age, 'employee_age'),
        (employee_birthdate, 'employee_birthdate'),
        (employee_maritalstatus, 'employee_maritalstatus'),
        (employee_home_address_line_1, 'employee_home_address_line_1'),
        (employee_home_address_line_2, 'employee_home_address_line_2'),
        (employee_home_city, 'employee_home_city'),
        (employee_home_state, 'employee_home_state'),
        (employee_home_zipcode, 'employee_home_zipcode'),
        (employee_mail_address_line_1, 'employee_mail_address_line_1'),
        (employee_mail_address_line_2, 'employee_mail_address_line_2'),
        (employee_mail_city, 'employee_mail_city'),
        (employee_mail_state, 'employee_mail_state'),
        (employee_mail_zipcode, 'employee_mail_zipcode'),
        (employee_work_address_line_1, 'employee_work_address_line_1'),
        (employee_work_address_line_2, 'employee_work_address_line_2'),
        (employee_work_city, 'employee_work_city'),
        (employee_work_state, 'employee_work_state'),
        (employee_work_zipcode, 'employee_work_zipcode'),
        (employee_email, 'employee_email'),
        (employee_alternate_email, 'employee_alternate_email'),
        (employee_home_phone, 'employee_home_phone'),
        (employee_work_phone, 'employee_work_phone'),
        (employee_mobile_phone, 'employee_mobile_phone'),
        (employee_enrollment_method, 'employee_enrollment_method'),
        (employee_employment_information, 'employee_employment_information'),
        (employer_name, 'employer_name'),
        (employer_description, 'employer_description'),
        (employer_FederalEmployerIdentificationNumber, 'employer_FederalEmployerIdentificationNumber'),
        (employer_CarrierMasterAgreementNumber, 'employer_CarrierMasterAgreementNumber'),
        (employer_address_line_1, 'employer_address_line_1'),
        (employer_address_line_2, 'employer_address_line_2'),
        (employer_city, 'employer_city'),
        (employer_state, 'employer_state'),
        (employer_zipcode, 'employer_zipcode'),
        (employer_purpose, 'employer_purpose'),
        (employer_planadmin_email, 'employer_planadmin_email'),
        (product_name, 'product_name'),
        (product_type, 'product_type'),
        (product_description, 'product_description'),
        (product_coverage_limit, 'product_coverage_limit'),
        (product_price_per_1000_units, 'product_price_per_1000_units'),
        (transmission_SenderName, 'transmission_SenderName'),
        (transmission_BenefitAdministratorPlatform, 'transmission_BenefitAdministratorPlatform'),
        (transmission_ReceiverName, 'transmission_ReceiverName'),
        (transmission_TestProductionCode, 'transmission_TestProductionCode'),
        (transmission_TransmissionTypeCode, 'transmission_TransmissionTypeCode'),
        (transmission_SystemVersionIdentifier, 'transmission_SystemVersionIdentifier'),
        (transmission_planadmin_email, 'transmission_planadmin_email')
    )

#Required indicator
    YES = 'Yes'
    NO = 'No'

    CODE_CHOICES = (
        (YES, 'Yes'),
        (NO, 'No')
    )

    attributes = models.CharField(max_length=100,
                                      choices=CHOICES,
                                      default='Unknown')

    numberfield = models.CharField(max_length=100,
                                      choices=CODE_CHOICES,
                                      default=NO)
    create_date = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="numcheck_rule_creator_set")

    def __str__(self):
        return self.attributes

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("numchecks:single", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-create_date"]
