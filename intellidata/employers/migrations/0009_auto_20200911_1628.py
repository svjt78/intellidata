# Generated by Django 3.0.8 on 2020-09-11 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employers', '0008_auto_20200911_1617'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employererroraggregate',
            old_name='total_employees_till_date',
            new_name='total_employers_till_date',
        ),
    ]
