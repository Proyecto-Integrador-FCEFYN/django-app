# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2022-09-19 23:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_auto_20220817_1652'),
        ('events', '0003_auto_20220817_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='permittedaccess',
            name='device',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='devices.Device'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='webopendoor',
            name='device',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='devices.Device'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='button',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='devices.Device'),
        ),
        migrations.AlterField(
            model_name='deniedaccess',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='devices.Device'),
        ),
    ]