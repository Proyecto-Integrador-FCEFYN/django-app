# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2022-08-17 22:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20220628_1825'),
    ]

    operations = [
        migrations.AddField(
            model_name='button',
            name='device',
            field=models.TextField(default='', verbose_name='Device'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='deniedaccess',
            name='device',
            field=models.TextField(default=None, verbose_name='Device'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='movement',
            name='device',
            field=models.TextField(default='', verbose_name='Device'),
            preserve_default=False,
        ),
    ]