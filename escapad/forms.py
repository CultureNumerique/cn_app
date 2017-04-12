#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import logging

from django import forms
from django.utils.translation import ugettext as _

logger = logging.getLogger(__name__)



class RepositoryForm(forms.ModelForm):
    
    def clean(self):
        cleaned_data = super(RepositoryForm, self).clean()
        print("cleaned_data = %s " % cleaned_data)
        success = True
        if cleaned_data['git_url']:
            try:
                res = requests.get(cleaned_data['git_url'])
                if not (res.status_code == 200):
                    success = False 
            except Exception as e:
                logger.error("Error when checking url \n\t %s" % (e)) 
                success = False
            if not success:
                raise forms.ValidationError(
                    _('Git URL invalide %(url)s '),
                    code='invalid_url',
                    params={'url': cleaned_data['git_url'] },
                )
            else:
                return

class ContactForm(forms.Form):

    sujet = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    envoyeur = forms.EmailField(label="Votre adresse mail")
    renvoi = forms.BooleanField(help_text="Cochez si vous souhaitez obtenir une copie du mail envoyé.", required=False)
    photo = forms.FileField()

class UploadForm(forms.Form):

    nom_projet = forms.CharField(max_length=100)
    home = forms.FileField()
    #logo = forms.ImageField()
    module = forms.FileField()
    




         
