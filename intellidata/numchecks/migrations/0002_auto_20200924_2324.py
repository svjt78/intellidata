# Generated by Django 3.0.8 on 2020-09-25 03:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('numchecks', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='numcheck',
            options={'ordering': ['-create_date']},
        ),
    ]