from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from escapad.models import Repository



class Cours(models.Model):
    nom_cours = models.CharField(max_length=30)
    id_cours = models.CharField(max_length=30, primary_key=True)
    url_home = models.CharField(max_length=30)
    def __str__(self):
        #return "Cours nomme {0}, Profil associe: {1}".format(self.nom_cours, self.profil_set.all())
        return "Cours: {0} ({1} module(s), {2} contributeur(s))".format(self.nom_cours, len(self.module_set.all()),len(self.profil_set.all()))


class Module(models.Model):
    url = models.CharField(max_length=30, primary_key=True)
    nom_module = models.CharField(max_length=30)
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    def __str__(self):
        return "Module: {0} (Cours: {1})".format(self.nom_module, self.cours.id_cours)


class Profil(models.Model):
    user = models.OneToOneField(User)  # La liaison OneToOne vers le modele User
    cours = models.ManyToManyField(Cours, blank=True)
    repositories = models.ManyToManyField(Repository)
    def __str__(self):
        return "Profil: {0} ({1} cours, {2} repositories)".format(self.user.username,len(self.cours.all()),len(self.repositories.all()))
