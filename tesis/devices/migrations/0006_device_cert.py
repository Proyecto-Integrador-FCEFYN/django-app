# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2022-11-02 02:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_auto_20220817_1652'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='cert',
            field=models.CharField(default=1, max_length=4096, verbose_name='Certificado'),
            preserve_default=False,
        ),
    ]
