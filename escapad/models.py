# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from django.db import models
from django.utils.text import slugify

from django.contrib.auth.models import User

# regexs
reGit = re.compile('http[s]*://(?P<provider>.*?)/(?P<user>.*?)/(?P<repo>[^/]*?)(/|$)')


class Repository(models.Model):

    def set_name(self, url):
        try:
            name = url.strip('/').rsplit('/', 1)[-1].strip('.git').lower()
        except Exception as e:
            name = "default_name"
        return name

    def set_user(self, url):
        try:
            user = url.strip('/').rsplit('/', 2)[-2].lower()
        except Exception as e:
            user = "default_user"
        return user

    def set_provider(self, url):
        try:
            provider = url.strip('/').rsplit('/', 3)[-3].lower()
        except Exception as e:
            provider = "http://github.com"
        return provider

    @staticmethod
    def set_slug(url):
        try:
            slug = slugify(url.rstrip('/').lstrip('https://').
                           replace('.', '-').replace('/', '_').lower())
        except Exception as e:
            slug = slugify(url)
        return slug

    def save(self, *args, **kwargs):
        """populate some fields from git url before saving,
           but only when creating new objects
        """
        if self.pk is None:  # this is true when object does not exist yet
            # use regex to retrieve infos
            self.slug = self.set_slug(self.git_url)
            fieldsReg = reGit.search(self.git_url)
            if fieldsReg:
                self.git_name = fieldsReg.group('repo') if fieldsReg.group('repo') else "default_name"
                self.git_username = fieldsReg.group('user') if fieldsReg.group('user') else "default_user"
                self.provider = fieldsReg.group('provider') if fieldsReg.group('provider') else "github.com"
        super(Repository, self).save(*args, **kwargs)

    git_url = models.URLField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)
    git_name = models.CharField(max_length=200, blank=True, null=True)
    git_username = models.CharField(max_length=200, blank=True, null=True)
    default_branch = models.CharField(max_length=200, blank=True,
                                      null=True, default="master")
    last_compiled = models.DateTimeField(blank=True, null=True)
    repo_synced = models.BooleanField(default=False)
    show_feedback = models.BooleanField(default=False)
    provider = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return "Repository: {0} (user: {1})".format(self.git_name, self.git_username)


class Cours(models.Model):
    nom_cours = models.CharField(max_length=30)
    id_cours = models.CharField(max_length=30, primary_key=True)
    url_home = models.CharField(max_length=30)

    def __str__(self):
        return "Cours: {0} ({1} module(s), {2} contributeur(s))".format(self.nom_cours,
                                                                        len(self.module_set.all()),
                                                                        len(self.profil_set.all()))


class Module(models.Model):
    url = models.CharField(max_length=30, primary_key=True)
    nom_module = models.CharField(max_length=30)
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)

    def __str__(self):
        return "Module: {0} (Cours: {1})".format(self.nom_module,
                                                 self.cours.id_cours)


class Profil(models.Model):
    user = models.OneToOneField(User)
    cours = models.ManyToManyField(Cours, blank=True)
    repositories = models.ManyToManyField(Repository)

    def __str__(self):
        return "Profil: {0} ({1} cours, {2} repositories)".format(self.user.username,
                                                                  len(self.cours.all()),
                                                                  len(self.repositories.all()))
