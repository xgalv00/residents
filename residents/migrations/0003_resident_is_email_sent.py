# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-14 13:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('residents', '0002_residentlog_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='resident',
            name='is_email_sent',
            field=models.BooleanField(default=False),
        ),
    ]
