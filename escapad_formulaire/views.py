#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import json
import mimetypes
import logging
import os
import shlex
import subprocess
import sys
import tarfile

import forms
from lxml import etree

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.generic import View

from django.contrib.auth import authenticate, login, logout

logger = logging.getLogger(__name__)

from .forms import *
from .models import *
from django.contrib.auth.forms import PasswordChangeForm


from src import model
from src import utils
from src import cnExportLight as cn

import markdown
import StringIO
import urllib2
import os

#RANDOM
import string
import random
import re
from cn_app.settings import ETHERPAD_URL
from cn_app.settings import API_KEY

#################################
#                               #
#        SIMPLE FORMS VIEWS     #
#                               #
#################################


def form_upload(request):
    """
    View creating archive using a simple form with inputs only (no etherpad).
    Each module is composed of a markdown file, and a media folder.
    1. Get each markdown file and media data from the forms.
    2. Extract the medias into StringIO lists
    3. Generate the course archive
    """
    sauvegarde = False

    form = UploadForm(request.POST or None, request.FILES or None)
    formMod = ModuleForm(request.POST or None, request.FILES or None)

    if form.is_valid() and formMod.is_valid():

        homeData=form.cleaned_data["home"]
        titleData=form.cleaned_data["nom_cours"]
        logoData=form.cleaned_data["logo"]
        feedback=form.cleaned_data["feedback"]

        modulesData=[]
        mediasData=[]
        mediasType=[]
        nbModule=request.POST.get("nb_module")

        #Go through each modules to get the md and media data
        for i in range(1, int(nbModule)+1):
            nomModule="module_"+str(i)
            nomMedia="media_"+str(i)
            moduleData=request.FILES.get(nomModule)
            mediaData=request.FILES.get(nomMedia)


            modulesData.append(moduleData)
            mediasData.append(mediaData)

            if mediaData:
                mediaName=request.FILES.get(nomMedia).name
                # Specify if the media is empty or not (tar.gz or empty)
                if re.match(r"^.*\.tar\.gz",mediaName):
                    mediasType.append("application/octet-stream")
                elif re.match(r"^.*\.zip",mediaName):
                    mediasType.append("application/zip")
                else:
                    mediasType.append('None')
            else:
                mediasType.append('None')

        mediasDataObj,mediasNom=cn.extractMediaArchive(mediasData, mediasType)

        zip=cn.generateArchive(modulesData, mediasDataObj, mediasNom, homeData, titleData, logoData, feedback)

        sauvegarde = True

        response= HttpResponse(zip)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = "attachment; filename=\""+titleData+".zip\""
        return response

    return render(request, 'escapad_formulaire/form.html', {
        'form': form,
        'formMod': formMod,
        'sauvegarde': sauvegarde
    })


def form_upload_light(request):
    """
        View requesting an archive already made by the user
        Generate directly the website by calling generateArchiveLight
    """
    sauvegarde = False
    erreurs =[]
    form = UploadFormLight(request.POST or None, request.FILES or None)

    if form.is_valid() :
        repoDir = settings.BASE_DIR
        outDir = settings.BASE_DIR
        baseUrl = settings.BASE_DIR

        archiveData = form.cleaned_data["archive"]
        archiveName = form.cleaned_data["archive"].name
        feedback = form.cleaned_data["feedback"]

        archiveType = "None"
        if re.match(r"^.*\.tar\.gz",archiveName):
            archiveType = "application/octet-stream"
        elif re.match(r"^.*\.zip",archiveName):
            archiveType = "application/zip"


        zip,title,erreurs=cn.generateArchiveLight(archiveData, archiveType, feedback)

        sauvegarde = True

        if not erreurs:
            response= HttpResponse(zip)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = "attachment; filename=\""+title+".zip\""
            return response

    return render(request, 'escapad_formulaire/formlight.html', {
        'form': form,
        'sauvegarde': sauvegarde,
        'erreurs': erreurs
    })



def form_reupload(request):
    """
        View allowing the user to reupload a course with the export.tar.gz provided when generating a course
        1. Open the export.tar.gz archive
        2. Get course infos from infos.xml and create a Course object (generate home_url)
        3. Add the home content to a new pad
        4. For each module: Generate with module_url, put it into a Module object, and add the module to the course
        5. For each module: Add the module content to a new pad
        6. Link the course to the current user, and redirect to his home page.
    """

    if not request.user.is_authenticated:
        return redirect(connexion)

    myUser=request.user

    # For those who subscribe with django shell command (createsuperuser...)
    # Create and associate a profile to the user.
    try:
        profil = Profil.objects.get(user=myUser)
    except Profil.DoesNotExist:
        profil = Profil(user=myUser)
        profil.save()

    sauvegarde = False
    erreurs = []
    modules_obj=[]

    form = ReUploadForm(request.POST or None, request.FILES or None)

    if form.is_valid() :
        repoDir=settings.BASE_DIR
        outDir=settings.BASE_DIR
        baseUrl=settings.BASE_DIR

        tarArchiveIO = StringIO.StringIO(form.cleaned_data["archive"].read())

        # We open the tar archive inside of the StringIO instance
        with tarfile.open(mode='r:gz', fileobj=tarArchiveIO) as tar:
            #for each EDX element belonging to the module

            try:
                xmlFile = tar.extractfile("infos.xml")
                tree = etree.parse(xmlFile)

                # Get the course infos
                cours=tree.xpath("/cours")[0]
                nom=cours.getchildren()[0].text

                # Generate the course and associate with the current user
                id_cours = id_generator()
                url_home = 'home-'+id_generator()
                cours_obj = Cours(nom_cours=nom, id_cours=id_cours, url_home=url_home)

                try:
                    # Generate home
                    homeFile= tar.extractfile("home.md")
                    content=homeFile.read()
                    # Prepare the string to be sent via curl to etherpad
                    content=content.replace('\"','\\\"')
                    content=content.replace('`','\\`')
                    # Ask etherpad to create a new pad with the string
                    os.system("curl -X POST -H 'X-PAD-ID:"+ url_home+"' " +ETHERPAD_URL+"post")
                    os.system("curl -X POST --data \""+content+"\" -H 'X-PAD-ID:"+ url_home +"' " +ETHERPAD_URL+"post")
                except KeyError:
                    erreurs.append("Erreur de structure: Impossible de trouver home.md !");

                # Generate each module
                cpt=1
                modules_obj=[]
                for nomMod in zip(tree.xpath("/cours/module/nomModule")):
                    try:
                        moduleFile= tar.extractfile("module"+str(cpt)+".md")
                        url = 'module-'+id_generator()
                        nom_module = nomMod[0].text
                        module_obj = Module(url=url, nom_module=nom_module, cours=cours_obj)
                        modules_obj.append(module_obj)

                        content=moduleFile.read()
                        # Prepare the string to be sent via curl to etherpad
                        content=content.replace('\"','\\\"')
                        content=content.replace('`','\\`')
                        # Ask etherpad to create a new pad with the string
                        os.system("curl -X POST -H 'X-PAD-ID:"+ url +"' " +ETHERPAD_URL+"post")
                        os.system("curl -X POST --data \""+content+"\" -H 'X-PAD-ID:"+ url +"' " +ETHERPAD_URL+"post")
                    except KeyError:
                        erreurs.append("Erreur de structure: Impossible de trouver module"+str(cpt)+".md ! \n")
                    cpt+=1

            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver infos.xml ! \n")


            tar.close()
        if not erreurs:

            # we can save if there's no errors
            cours_obj.save()
            profil.cours.add(cours_obj)
            profil.save()

            for module_obj in modules_obj:
                module_obj.save()

            return redirect(mes_cours)

    return render(request, 'escapad_formulaire/formreupload.html', {
        'form': form,
        'sauvegarde': sauvegarde,
        'erreurs' : erreurs
    })

######################################
#                                    #
#           PREVIEW VIEWS            #
#                                    #
######################################



def apercu_module(request,id_export,feedback):
    """
        View showing the preview of a module using the culture-numerique css
        1. Get the content of the pad with urllib2
        2. Generate the module with the content
        3. parse the module in a variable
        4. render the HTML with the variable

        :param id_export: pad id
        :param feedback: do we want a feedback on the preview?
    """
    url=ETHERPAD_URL+"p/"+id_export+"/export/txt"
    response = urllib2.urlopen(url)

    feedback = feedback!="0"

    moduleData= StringIO.StringIO(response.read())
    MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
    module = model.Module(moduleData, "module", "base")

    home_html = ''
    for sec in (module.sections):
        home_html += "\n\n<!-- Section "+sec.num+" -->\n"
        home_html += "\n\n<h1> "+sec.num+". "+sec.title+" </h1>\n";
        for sub in (sec.subsections):
            home_html += "\n\n<!-- Subsection "+sub.num+" -->\n"
            home_html += "\n\n<h2>"+sub.num+". "+sub.title+" </h2>\n"
            home_html += sub.toHTML(feedback)

    return render(request, 'escapad_formulaire/apercu_module.html', {
        'res': home_html
    })

# View showing the preview of a home page using the culture-numerique css
# require the pad id
def apercu_home(request,id_export):
    """
        View showing the preview of a home page using the culture-numerique css
        1. Get the content of the pad with urllib2
        2. Simply parse the content in a variable (with the native python method markdown)
        3. Render the HTML with the variable

        :param id_export: pad id
    """
    url=ETHERPAD_URL+"p/"+id_export+"/export/txt"

    response = urllib2.urlopen(url)

    moduleData= response.read()
    MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
    home_html = markdown.markdown(moduleData, MARKDOWN_EXT)

    return render(request, 'escapad_formulaire/apercu_home.html', {
        'res': home_html
    })


#################################
#                               #
#         FORMS WITH MODEL      #
#                               #
#################################

# id generator for the projects
def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def mes_cours(request):
    """
        View resuming the user's courses
        The user can either access an existing course, or create a new one
    """
    if not request.user.is_authenticated:
        return redirect(connexion)

    myUser=request.user

    # For those who subscribe with django shell command (createsuperuser...)
    # Create and associate a profile to the user.
    try:
        profil = Profil.objects.get(user=myUser)
    except Profil.DoesNotExist:
        profil = Profil(user=myUser)
        profil.save()

    #profil= Profil.objects.get(user=myUser)
    form = CreateNew(request.POST or None)
    if form.is_valid() :
        url_home='home-'+id_generator()
        id_cours=id_generator()
        cours=Cours(id_cours=id_cours, nom_cours=form.cleaned_data['nom'], url_home=url_home)
        cours.save()
        profil.cours.add(cours)

    return render(request, 'escapad_formulaire/liste_cours.html', {
        'profil' : profil,
        'form' : form
    })



def cours(request, id_cours):
    """
        View showing the information of a course.
        Possible actions:
        1. Create a new module
        2. Adding a user to the course
        3. Generating the course
            For each module belonging to the course object, we call urlib2 to get the content.
            Then put this content into a StringIO.
            We write the xml course file.
            Then we generate the course

        :param id_cours: id du cours
    """

    # if the user is authenticated
    if not request.user.is_authenticated:
        return redirect(connexion)

    try:
        cours = Cours.objects.get(id_cours=id_cours)
        request.user.profil.cours.get(id_cours=id_cours)
    except Cours.DoesNotExist:
        return redirect(mes_cours)

    # if the course doesn't belong to the user
    if not request.user.profil.cours.get(id_cours=id_cours):
        return redirect(mes_cours)


    form_new_module = CreateNew(request.POST or None)
    form_generate = GenerateCourseForm(request.POST or None, request.FILES or None)
    form_add_user = SearchUser(request.POST or None)

    userFound = False

    # Create a new module
    if form_new_module.is_valid() and request.POST['id_form'] == '0':
        url = 'module-'+id_generator()
        nom=request.POST['nom']
        module = Module(nom_module=nom, url=url, cours=cours)
        module.save()
        cours.save()

    # Adding a user to the course
    elif form_add_user.is_valid() and request.POST['id_form'] == '1':
        user = User.objects.get(username = form_add_user.cleaned_data['user'])
        profil = user.profil
        profil.cours.add(cours)
        userFound = True

    # Generating the course
    elif form_generate.is_valid() and request.POST['id_form'] == '2':
        repoDir=settings.BASE_DIR
    	outDir=settings.BASE_DIR
    	baseUrl=settings.BASE_DIR

        titleData=cours.nom_cours
        logoData=form_generate.cleaned_data["logo"]
        medias=form_generate.cleaned_data["medias"]
        feedback=form_generate.cleaned_data["feedback"]

        #url to export the pad into markdown file
        url_home=ETHERPAD_URL+'p/'+cours.url_home+'/export/txt'

        # Get the text from the etherpad instance
        # We need to create a hidden input storing the plain text exporting url.
        # The url looks like this: http://<etherpad-url>/p/<pad-url>/export/txt
        response = urllib2.urlopen(url_home)
        homeData = StringIO.StringIO(response.read())

        modulesData=[]
        mediasData=[]
        archiveType="None"
        if medias:
            mediasName=form_generate.cleaned_data["medias"].name
            if re.match(r"^.*\.tar\.gz",mediasName):
                archiveType="application/octet-stream"
            elif re.match(r"^.*\.zip",mediasName):
                archiveType="application/zip"




        #for each modules from the course
        for module in cours.module_set.all():
            # get the pad content
            url_module= ETHERPAD_URL+'p/'+module.url+'/export/txt'
            response = urllib2.urlopen(url_module)
            moduleData = StringIO.StringIO(response.read())
            modulesData.append(moduleData)
        mediasData, mediasNom=cn.getMediasDataFromArchive(medias, archiveType, len(cours.module_set.all()))

        xmlCourse=cn.writeXMLCourse(cours)
        zip=cn.generateArchive(modulesData,mediasData,mediasNom,homeData,titleData,logoData, feedback, xmlCourse)

        response= HttpResponse(zip)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = "attachment; filename=\"site.zip\""
        return response

    cours=Cours.objects.get(id_cours=id_cours)

    return render(request, 'escapad_formulaire/cours.html', {
        'cours' : cours,
        'form_new_module' : form_new_module,
        'form_generate' : form_generate,
        'form_add_user' : form_add_user,
        'userFound' : userFound

    })


def cours_edition(request, id_cours ,url):
    """
        View to edit a module/home.
        Security check: if there's a problem in the course_id or url_id,
        we redirect the user to its home page.

        :param id_cours: id du cours
        :param url: url du module
    """

    if not request.user.is_authenticated:
        return redirect(connexion)

    # Check if the user has the right to be on this page
    try:
        cours = Cours.objects.get(id_cours=id_cours)
        request.user.profil.cours.get(id_cours=id_cours)
    except Cours.DoesNotExist:
        return redirect(mes_cours)

    is_home=True
    name=''
    # url starting with module: check it it belongs to the course
    if re.match(r"^module",url):
        # Check if the module exists
        try:
            module=cours.module_set.get(url=url)
        except Module.DoesNotExist:
            return redirect(mes_cours)
        name=module.nom_module
        #url_media = module.url_media
        is_home = False

    # url starting with home: check if it is equal to the course url_home
    elif re.match(r"^home",url):
        name="home"
        #url_media = cours.url_media
        if cours.url_home != url:
            return redirect(mes_cours)
    # the url doesn't start with "home" nor "module", there is no chance it belongs to the application
    else:
        return redirect(mes_cours)

    full_url = ETHERPAD_URL+'p/'+url

    return render(request, 'escapad_formulaire/form_edition.html', {
        'id_cours': id_cours,
        'url': url,
        'full_url': full_url,
        'name': name,
        'is_home': is_home
    })


def delete_module(request, id_cours, url):
    """
        Delete a module from a course. Irreversible task.
        (This is here we need the API_KEY, it is required to delete a pad from an url)

        :param id_cours: course id
        :param url: url of the module/home
    """
    if not request.user.is_authenticated:
        return redirect(connexion)

    # Check if the course exists
    try:
        course = Cours.objects.get(id_cours=id_cours)
        request.user.profil.cours.get(id_cours=id_cours)
    except Cours.DoesNotExist:
        return redirect(mes_cours)

    # Check if the module exists
    try:
        module=course.module_set.get(url=url)
        #module= Module.objects.get(url=url)
    except Module.DoesNotExist:
        return redirect(mes_cours)

    # Delete the pad
    response = urllib2.urlopen(ETHERPAD_URL+"api/1/deletePad?apikey="+API_KEY+"&padID="+url)

    # Delete the module model and update the course model
    module.delete()
    c= Cours.objects.get(id_cours=id_cours)
    c.save()
    return redirect(cours,id_cours=id_cours)


def delete_course(request, id_cours):
    """
        Delete a course, then redirect the user to its course list page
        Note: If a course is shared by several user, the course will not be deleted,
        we will just remove the ManyToManyField relation between the user and the course

        :param id_cours: course_id

    """
    if not request.user.is_authenticated:
        return redirect(connexion)

    # Check if the course exists
    try:
        course = Cours.objects.get(id_cours=id_cours)
        request.user.profil.cours.get(id_cours=id_cours)
    except Cours.DoesNotExist:
        return redirect(connexion)

    # delete the home pad
    response = urllib2.urlopen(ETHERPAD_URL+"api/1/deletePad?apikey="+API_KEY+"&padID="+course.url_home)

    # Only one contributor to the course: We delete it entirely.
    if len(course.profil_set.all()) == 1:
        # delete the pads belonging to the course
        for module in course.module_set.all():
            response = urllib2.urlopen(ETHERPAD_URL+"api/1/deletePad?apikey="+API_KEY+"&padID="+module.url)
            module.delete()
        course.delete()
    # More than one contributor: We remove the link between the current user and the course.
    else:
        profil=request.user.profil
        course.profil_set.remove(profil)
    return redirect(mes_cours)

#################################
#                               #
#     REPOSITORIES INTERFACE    #
#                               #
#################################

def my_repositories(request):
    if not request.user.is_authenticated:
        return redirect(connexion)

    form_new_repo = CreateRepository(request.POST or None)

    myUser=request.user
    profil = Profil.objects.get(user=myUser)
    repositories=profil.repositories

    if form_new_repo.is_valid() :
        git_url = form_new_repo.cleaned_data['git_url']
        default_branch = form_new_repo.cleaned_data['default_branch']
        feedback = form_new_repo.cleaned_data['feedback']

        # Check if the repository exists, create it if not
        try:
            repo = Repository.objects.get(git_url=git_url)
        except Repository.DoesNotExist:
            repo = Repository(git_url=git_url, default_branch=default_branch, show_feedback=feedback)
            repo.save()

        # Check if the repository belong to the user.
        try:
            profil.repositories.get(git_url=git_url)
            repo = Repository.objects.get(git_url=git_url)
        except Repository.DoesNotExist:
            profil.repositories.add(repo)



    return render(request, 'escapad_formulaire/my_repositories.html', {
        'repositories': repositories,
        'user': myUser,
        'profil': profil,
        'form': form_new_repo
    })

def repository(request, slug):
    if not request.user.is_authenticated:
        return redirect(connexion)

    # Check if the course exists
    try:
        repo = Repository.objects.get(slug=slug)
        request.user.profil.repositories.get(slug=slug)
    except Repository.DoesNotExist:
        return redirect(connexion)

    repo = Repository.objects.get(slug=slug)

    form_repo = ModifyRepository(request.POST or None, instance=repo)

    if form_repo.is_valid() :
        def_branch = form_repo.cleaned_data['default_branch']
        feedbk = form_repo.cleaned_data['show_feedback']

        repo = Repository.objects.get(slug=slug)
        repo.default_branch = def_branch
        repo.show_feedback = feedbk
        repo.save()

    return render(request, 'escapad_formulaire/repository.html', {
        'repository' : repo,
        'form' : form_repo,
    })




def delete_repository(request, slug):

    if not request.user.is_authenticated:
        return redirect(connexion)

    # Check if the course exists
    try:
        repo = Repository.objects.get(slug=slug)
        request.user.profil.repositories.get(slug=slug)
    except Cours.DoesNotExist:
        return redirect(connexion)

    # Only one contributor to the course: We delete it entirely.
    if len(repo.profil_set.all()) == 1:
        repo.delete()
    # More than one contributor: We remove the link between the current user and the course.
    else:
        profil=request.user.profil
        repo.profil_set.remove(profil)

    return redirect(my_repositories)


#################################
#                               #
#  CONNEXION AND SUBSCRIPTION   #
#                               #
#################################


def connexion(request):
    """
        Connexion View
    """
    error = False
    if request.method == "POST":
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)  # Nous vérifions si les données sont correctes
            if user:  # Si l'objet renvoyé n'est pas None
                login(request, user)  # nous connectons l'utilisateur
            else: # sinon une erreur sera affichée
                error = True
    else:
        form = ConnexionForm()

    return render(request, 'escapad_formulaire/connexion.html', locals())


def inscription(request):
    """
        View for creating a new user on the user side
        The form create a user (Django native class), and associate him to a profile, which will contain the user's projects
    """
    error = False
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save();
            return redirect(connexion)
        else: # sinon une erreur sera affichée
            error = True
    else:
        form = CreateUserForm()

    return render(request, 'escapad_formulaire/inscription.html', locals())


def deconnexion(request):
    """
        Disconnecting view
    """
    logout(request)
    return redirect(reverse(connexion))
