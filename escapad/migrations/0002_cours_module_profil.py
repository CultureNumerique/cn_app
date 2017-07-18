# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-17 21:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('escapad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cours',
            fields=[
                ('nom_cours', models.CharField(max_length=30)),
                ('id_cours', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('url_home', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('url', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('nom_module', models.CharField(max_length=30)),
                ('cours', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='escapad.Cours')),
            ],
        ),
        migrations.CreateModel(
            name='Profil',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cours', models.ManyToManyField(blank=True, to='escapad.Cours')),
                ('repositories', models.ManyToManyField(to='escapad.Repository')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]