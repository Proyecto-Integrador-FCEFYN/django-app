# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2022-08-16 23:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20220812_2258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='category_list',
            field=models.ManyToManyField(blank=True, related_name='user_category_list', to='users.Category', verbose_name='Categoria'),
        ),
    ]
