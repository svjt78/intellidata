# Generated by Django 3.0.8 on 2020-09-03 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0006_employee_employerid'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeerror',
            name='sendername',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='employeeerror',
            name='transmissionid',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
