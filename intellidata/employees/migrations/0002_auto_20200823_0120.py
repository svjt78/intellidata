# Generated by Django 3.0.8 on 2020-08-23 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='backend_SOR_connection',
            field=models.CharField(blank=True, default='Disconnected', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='commit_indicator',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='source',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employeeerror',
            name='source',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employeeerroraggregate',
            name='source',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]