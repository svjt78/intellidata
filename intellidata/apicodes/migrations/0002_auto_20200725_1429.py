# Generated by Django 3.0.8 on 2020-07-25 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apicodes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apicodes',
            name='http_error_category',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='apicodes',
            name='http_response_code',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='apicodes',
            name='http_response_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
