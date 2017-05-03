# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-02 08:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escapad_formulaire', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profil',
            name='site_web',
        ),
        migrations.RemoveField(
            model_name='projet',
            name='user',
        ),
        migrations.AddField(
            model_name='profil',
            name='projets',
            field=models.ManyToManyField(to='escapad_formulaire.Projet'),
        ),
    ]