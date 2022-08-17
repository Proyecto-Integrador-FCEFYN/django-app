# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2022-08-17 19:52
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0004_device_last_ping'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='ip_address',
            field=models.CharField(max_length=50, verbose_name='Dirección IP u hostname'),
        ),
        migrations.AlterField(
            model_name='device',
            name='port',
            field=models.CharField(max_length=5, validators=[django.core.validators.RegexValidator(re.compile('^[0-9]*$', 32), 'Ingrese un número de puerto válido.')], verbose_name='Puerto'),
        ),
    ]
