# Generated by Django 3.0.8 on 2020-09-11 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employers', '0005_auto_20200910_2323'),
    ]

    operations = [
        migrations.AddField(
            model_name='employererroraggregate',
            name='sendername',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
