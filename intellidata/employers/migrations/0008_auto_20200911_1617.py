# Generated by Django 3.0.8 on 2020-09-11 20:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employers', '0007_auto_20200911_0056'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employererroraggregate',
            old_name='clean',
            new_name='number_of_error_occurences',
        ),
        migrations.RenameField(
            model_name='employererroraggregate',
            old_name='error',
            new_name='processed_clean',
        ),
        migrations.RenameField(
            model_name='employererroraggregate',
            old_name='total',
            new_name='total_employees_till_date',
        ),
    ]