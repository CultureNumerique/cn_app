# -*- coding: utf-8 -*-
import requests
import logging

from django import forms
from django.utils.translation import ugettext as _

from .models import User
from .models import Profil
from escapad.models import Repository

import re

logger = logging.getLogger(__name__)

isTarFile = r'.*\.tar\.gz$'
isZipFile = r'.*\.zip$'


class RepositoryForm(forms.ModelForm):

    def clean(self):
        """Clean is called right after submitting form and before performing
        actual submission We override it to check that the git url
        provided returns a 200 response
        """
        cleaned_data = super(RepositoryForm, self).clean()
        # Process check only when adding object.
        # In the edit admin page 'git_url' is set as read-only
        # and hence is not loaded in the form validation object
        if not self.instance.git_url:
            success = True
            if cleaned_data['git_url']:
                # check git_url returns 200
                try:
                    res = requests.get(cleaned_data['git_url'])
                    if not (res.status_code == 200):
                        success = False
                except Exception as e:
                    logger.error("Error when checking url \n\t %s" % (e))
                    success = False
                # retrieve
                if not success:
                    raise forms.ValidationError(
                        _('Git URL invalide %(url)s '),
                        code='invalid_url',
                        params={'url': cleaned_data['git_url']},
                    )
                else:
                    return


class CreateNew(forms.Form):
    nom = forms.CharField(label="", max_length=100)


class SearchUser(forms.Form):
    user = forms.CharField(label="", max_length=100)

    # check if username does not already exists
    def clean_user(self):
        try:
            # get user from user model
            User.objects.get(username=self.cleaned_data['user'])
        except User.DoesNotExist:
            raise forms.ValidationError(
                _("l'utilisateur n'existe pas!"))
            return
        return self.cleaned_data['user']


class CourseProgram(forms.Form):
    courseTitle = forms.CharField(label=_("Nom du cours"), max_length=100)


class CourseOptions(forms.Form):
    logo = forms.ImageField(required=False)
    home = forms.FileField(label=_("Page d'accueil"), required=False)
    siteTemplate = forms.FileField(label="Modèle de site", required=False)
    moduleTemplate = forms.FileField(label="Modèle de module", required=False)
    feedback = forms.BooleanField(required=False)


class CourseModule(forms.Form):
    module_1 = forms.FileField()
    media_1 = forms.FileField(required=False)


class CourseFromArchive(forms.Form):
    archive = forms.FileField()
    feedback = forms.BooleanField(required=False)

    # check if the archive is a tar.gz archive
    def clean_archive(self):
        archiveName = self.cleaned_data['archive'].name
        if not re.match(isTarFile, archiveName) and not re.match(isZipFile, archiveName):
            raise forms.ValidationError(
                _("Veuillez utiliser une archive tar.gz ou zip!"))
            return
        return self.cleaned_data['archive']


class ReUploadForm(forms.Form):
    archive = forms.FileField(label="")

    # check if the archive is a tar.gz archive
    def clean_archive(self):
        archiveName = self.cleaned_data['archive'].name
        if not re.match(isTarFile,archiveName) and not re.match(isZipFile,archiveName):
            raise forms.ValidationError(
                _("Veuillez utiliser une archive tar.gz ou zip!"))
            return
        return self.cleaned_data['archive']


class UploadFormEth(forms.Form):
    nom_cours = forms.CharField(label=_("Nom du cours"), max_length=100)
    logo = forms.ImageField(required=False)


# Used for creating a course in a course view
class GenerateCourseForm(forms.Form):
    logo = forms.ImageField(required=False)
    medias = forms.FileField(required=False)
    siteTemplate = forms.FileField(required=False)
    moduleTemplate = forms.FileField(required=False)
    feedback = forms.BooleanField(required=False)

    # check if the archive is a tar.gz archive
    def clean_medias(self):
        if self.cleaned_data['medias']:
            archiveName = self.cleaned_data['medias'].name
            if not re.match(isTarFile,archiveName) and not re.match(isZipFile,archiveName):
                raise forms.ValidationError(
                    _("Veuillez utiliser une archive tar.gz ou zip !"))
                return
            return self.cleaned_data['medias']


class ModuleFormEth(forms.Form):
    media_1 = forms.FileField(required=False)


class CreateRepository(forms.Form):
    git_url = forms.CharField(label="Url git", max_length=50)
    default_branch = forms.CharField(label="Branche par défaut",
                                     max_length=30,
                                     initial="master")
    feedback = forms.BooleanField(required=False)

    def clean(self):
        success = True
        if self.cleaned_data['git_url']:
            # check git_url returns 200
            try:
                res = requests.get(self.cleaned_data['git_url'])
                if not (res.status_code == 200):
                    success = False
            except Exception as e:
                logger.error("Error when checking url \n\t %s" % (e))
                success = False
            # retrieve
            if not success:
                raise forms.ValidationError(
                    _('Git URL invalide %(url)s '),
                    code='invalid_url',
                    params={'url': self.cleaned_data['git_url']},
                )
            else:
                return


class ModifyRepository(forms.ModelForm):
    class Meta:
        model = Repository
        fields = '__all__'
        fields = ('default_branch', 'show_feedback')


class ConnexionForm(forms.Form):
    username = forms.CharField(label=_("Nom d'utilisateur"),
                               max_length=30)
    password = forms.CharField(label=_("Mot de passe"),
                               widget=forms.PasswordInput)


class CreateUserForm(forms.Form):
    username = forms.CharField(max_length=30,
                               label=_("Nom d'utilisateur"))
    first_name = forms.CharField(label=_("Nom"))
    last_name = forms.CharField(label="Prénom")
    password1 = forms.CharField(max_length=30,
                                widget=forms.PasswordInput(),
                                label=_("Mot de passe"))
    password2 = forms.CharField(max_length=30,
                                widget=forms.PasswordInput(),
                                label="Vérification")
    email = forms.EmailField(required=False)

    # check if username dos not exist before
    def clean_username(self):
        try:
            # get user from user model
            User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']

        raise forms.ValidationError("this user exist already")

    # check if username dos not exist before
    def clean_email(self):
        try:
            # get user from user model
            User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']

        # this email is already associated with an account
        raise forms.ValidationError(
            _("email déjà utilisé pour un autre compte"))

    # check if password 1 and password2 match each other
    def clean(self):
        # check if both pass first validation
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            # check if they match each other
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError("passwords dont match each other")

        return self.cleaned_data

    # create new user
    def save(self):
        new_profil = Profil()
        new_user = User.objects.create_user(self.cleaned_data['username'],
                                            self.cleaned_data['email'],
                                            self.cleaned_data['password1'])
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_profil.user = new_user

        new_user.save()
        new_profil.save()

        return new_profil
