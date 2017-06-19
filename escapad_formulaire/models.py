from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.contrib.auth.models import User


class Cours(models.Model):
    nom_cours = models.CharField(max_length=30)
    id_cours = models.CharField(max_length=30, primary_key=True)
    url_home = models.CharField(max_length=30)
    nb_module = models.IntegerField()
    def __str__(self):
        #return "Cours nomme {0}, Profil associe: {1}".format(self.nom_cours, self.profil_set.all())
        return "Cours-> {0}, {1} module(s), id: {2}, modules: {3}".format(self.nom_cours,self.nb_module, self.id_cours, self.module_set.all())


class Module(models.Model):
    url = models.CharField(max_length=30)
    nom_module = models.CharField(max_length=30)
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    def __str__(self):
        return "Module {0}".format(self.nom_module)


class Profil(models.Model):
    user = models.OneToOneField(User)  # La liaison OneToOne vers le modele User
    cours = models.ManyToManyField(Cours)

    def __str__(self):
        return "Profil de {0}, cours: {1}".format(self.user.username,self.cours.all())
