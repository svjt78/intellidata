from django import forms
from django.core.exceptions import ValidationError
from mandatories.models import Mandatory

CHOICES = (
    ('employee_ssn', 'employee_ssn'),
    ('employee_name', 'employee_name'),
    ('employee_gendercode', 'employee_gendercode'),
    ('employee_age', 'employee_age'),
    ('employee_birthdate', 'employee_birthdate'),
    ('employee_maritalstatus', 'employee_maritalstatus'),
    ('employee_home_address_line_1', 'employee_home_address_line_1'),
    ('employee_home_address_line_2', 'employee_home_address_line_2'),
    ('employee_home_city', 'employee_home_city'),
    ('employee_home_state', 'employee_home_state'),
    ('employee_home_zipcode', 'employee_home_zipcode'),
    ('employee_mail_address_line_1', 'employee_mail_address_line_1'),
    ('employee_mail_address_line_2', 'employee_mail_address_line_2'),
    ('employee_mail_city', 'employee_mail_city'),
    ('employee_mail_state', 'employee_mail_state'),
    ('employee_mail_zipcode', 'employee_mail_zipcode'),
    ('employee_work_address_line_1', 'employee_work_address_line_1'),
    ('employee_work_address_line_2', 'employee_work_address_line_2'),
    ('employee_work_city', 'employee_work_city'),
    ('employee_work_state', 'employee_work_state'),
    ('employee_work_zipcode', 'employee_work_zipcode'),
    ('employee_email', 'employee_email'),
    ('employee_alternate_email', 'employee_alternate_email'),
    ('employee_home_phone', 'employee_home_phone'),
    ('employee_work_phone', 'employee_work_phone'),
    ('employee_mobile_phone', 'employee_mobile_phone'),
    ('employee_enrollment_method', 'employee_enrollment_method'),
    ('employee_employment_information', 'employee_employment_information'),
    ('employer_name', 'employer_name'),
    ('employer_description', 'employer_description'),
    ('employer_FederalEmployerIdentificationNumber', 'employer_FederalEmployerIdentificationNumber'),
    ('employer_CarrierMasterAgreementNumber', 'employer_CarrierMasterAgreementNumber'),
    ('employer_address_line_1', 'employer_address_line_1'),
    ('employer_address_line_2', 'employer_address_line_2'),
    ('employer_city', 'employer_city'),
    ('employer_state', 'employer_state'),
    ('employer_zipcode', 'employer_zipcode'),
    ('employer_purpose', 'employer_purpose'),
    ('employer_planadmin_email', 'employer_planadmin_email'),
    ('product_name', 'product_name'),
    ('product_type', 'product_type'),
    ('product_description', 'product_description'),
    ('product_coverage_limit', 'product_coverage_limit'),
    ('product_price_per_1000_units', 'product_price_per_1000_units'),
    ('transmission_SenderName', 'transmission_SenderName'),
    ('transmission_BenefitAdministratorPlatform', 'transmission_BenefitAdministratorPlatform'),
    ('transmission_ReceiverName', 'transmission_ReceiverName'),
    ('transmission_TestProductionCode', 'transmission_TestProductionCode'),
    ('transmission_TransmissionTypeCode', 'transmission_TransmissionTypeCode'),
    ('transmission_SystemVersionIdentifier', 'transmission_SystemVersionIdentifier'),
    ('transmission_planadmin_email', 'transmission_planadmin_email')
    )

CODE_CHOICES = (
    ('YES', 'Yes'),
    ('NO', 'No')
    )


class MandatoryForm(forms.ModelForm):

    class Meta:
        model = Mandatory

        fields = ('attributes', 'required', 'description')

        widgets = {


        }
