# -*- coding: utf-8 -*-
import datetime
import logging
import os
import tarfile
from lxml import etree
import shutil
import string
import random
import re
import markdown
import StringIO
import urllib2


from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


from .models import Repository, Cours, Module, Profil
from .forms import UploadForm, UploadFormLight, ModuleForm, ReUploadForm, CreateNew, CreateUserForm, ConnexionForm, GenerateCourseForm, SearchUser, CreateRepository, ModifyRepository
from .utils import run_shell_command

from cn_app.settings import ETHERPAD_URL
from cn_app.settings import API_KEY

from src import model
from src import cnExportLight as cn

logger = logging.getLogger(__name__)


class BuildView(View):
    """
    A view for generating site from Repository
    """
    http_method_names = ['get', 'post']

    @csrf_exempt  # this is needed to allow unauthenticated access to this view
    def dispatch(self, *args, **kwargs):
        return super(BuildView, self).dispatch(*args, **kwargs)

    def build_repo(self, slug, request):
        # 1. cd to repo path
        repo_path = os.path.join(settings.REPOS_DIR, slug)
        build_path = os.path.join(settings.GENERATED_SITES_DIR, slug)
        base_url = os.path.join(settings.GENERATED_SITES_URL, slug)
        logger.warn("%s | Post to build view! repo_path = %s | Base URL = %s" %
                    (timezone.now(), repo_path, base_url))

        repo_object = Repository.objects.all().filter(slug=slug)[0]
        try:
            os.chdir(repo_path)
        except Exception as e:
            return {"success": "false",
                    "reason": "repo not existing, or not synced"}

        # 2. git pull origin [branch:'master']
        git_cmds = [("git checkout %s " % repo_object.default_branch),
                    ("git pull origin %s" % repo_object.default_branch)]
        for git_cmd in git_cmds:
            success, output = run_shell_command(git_cmd)
            if not(success):
                os.chdir(settings.BASE_DIR)
                return {"success": "false", "reason": output}

        # 3. build with BASE_PATH/src/toHTML.py
        os.chdir(settings.BASE_DIR)
        feedback_option = '-f' if repo_object.show_feedback else ''
        build_cmd = ("python src/cnExport.py -ie -r %s -d %s -u %s %s -L %s" %
                     (repo_path, build_path,
                      base_url, feedback_option, settings.LOGFILE))
        success, output = run_shell_command(build_cmd)
        # go back to BASE_DIR and check output
        os.chdir(settings.BASE_DIR)
        # FIXME: output should not be displayed for security reasons,
        # since it is logged internaly to debug.log
        if success:
            repo_object.last_compiled = datetime.datetime.now()
            repo_object.save()
            return({"success": "true", "output": output})
        else:
            return {"success": "false", "reason": output}

    def post(self, request, slug, *args, **kwargs):
        res = self.build_repo(slug, request)
        return JsonResponse(res)

    def get(self, request, slug, *args, **kwargs):
        self.build_repo(slug, request)
        return redirect(reverse('visit_site', args=(slug,)))


class BuildZipView(BuildView):
    """ View for building and zipping the whole archive before returning it"""

    def get(self, request, slug, *args, **kwargs):
        built = self.build_repo(slug, request)
        if built["success"] == "true":
            build_path = os.path.join(settings.GENERATED_SITES_DIR, slug)
            archive_name = shutil.make_archive(build_path, 'zip', build_path)
            zip_file = open(archive_name, 'r')
            response = HttpResponse(zip_file,
                                    content_type='application/force-download')
            response['Content-Disposition']='attachment; filename="%s.zip"' % slug
            return response
        else:
            return redirect(reverse('visit_site', args=(slug,)))


def visit_site(request, slug):
    """ Just a redirection to generated site """
    return redirect(os.path.join(settings.GENERATED_SITES_URL,
                                 slug,
                                 'index.html'))


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

        homeData = form.cleaned_data["home"]
        titleData = form.cleaned_data["nom_cours"]
        logoData = form.cleaned_data["logo"]
        feedback = form.cleaned_data["feedback"]

        modulesData = []
        mediasData = []
        mediasType = []
        nbModule = request.POST.get("nb_module")

        # Go through each modules to get the md and media data
        for i in range(1, int(nbModule)+1):
            nomModule = "module_"+str(i)
            nomMedia = "media_"+str(i)
            moduleData = request.FILES.get(nomModule)
            mediaData = request.FILES.get(nomMedia)

            modulesData.append(moduleData)
            mediasData.append(mediaData)

            if mediaData:
                mediaName = request.FILES.get(nomMedia).name
                # Specify if the media is empty or not (tar.gz or empty)
                if re.match(r"^.*\.tar\.gz", mediaName):
                    mediasType.append("application/octet-stream")
                elif re.match(r"^.*\.zip", mediaName):
                    mediasType.append("application/zip")
                else:
                    mediasType.append('None')
            else:
                mediasType.append('None')

        mediasDataObj, mediasNom = cn.extractMediaArchive(mediasData,
                                                          mediasType)

        zip = cn.generateArchive(modulesData,
                                 mediasDataObj,
                                 mediasNom,
                                 homeData,
                                 titleData,
                                 logoData,
                                 feedback)

        sauvegarde = True

        response = HttpResponse(zip)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = "attachment; filename=\"" + titleData+".zip\""
        return response

    # form upload light
    erreurs = []
    form2 = UploadFormLight(request.POST or None, request.FILES or None)

    if form2.is_valid():

        archiveData = form2.cleaned_data["archive"]
        archiveName = form2.cleaned_data["archive"].name
        feedback = form2.cleaned_data["feedback"]

        archiveType = "None"
        if re.match(r"^.*\.tar\.gz", archiveName):
            archiveType = "application/octet-stream"
        elif re.match(r"^.*\.zip", archiveName):
            archiveType = "application/zip"

        zip, title, erreurs = cn.generateArchiveLight(archiveData,
                                                      archiveType,
                                                      feedback)

        sauvegarde = True

        if not erreurs:
            response = HttpResponse(zip)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = "attachment; filename=\""+title+".zip\""
            return response

    return render(request, 'form.html', {
        'form': form,
        'formMod': formMod,
        'form2': form2,
        'sauvegarde': sauvegarde,
        'erreurs': erreurs
    })


def form_upload_light(request):
    """
        View requesting an archive already made by the user
        Generate directly the website by calling generateArchiveLight
    """
    sauvegarde = False
    erreurs = []
    form = UploadFormLight(request.POST or None, request.FILES or None)

    if form.is_valid():

        archiveData = form.cleaned_data["archive"]
        archiveName = form.cleaned_data["archive"].name
        feedback = form.cleaned_data["feedback"]

        archiveType = "None"
        if re.match(r"^.*\.tar\.gz", archiveName):
            archiveType = "application/octet-stream"
        elif re.match(r"^.*\.zip", archiveName):
            archiveType = "application/zip"

        zip, title, erreurs = cn.generateArchiveLight(archiveData,
                                                      archiveType,
                                                      feedback)

        sauvegarde = True

        if not erreurs:
            response = HttpResponse(zip)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = "attachment; filename=\""+title+".zip\""
            return response

    return render(request, 'formlight.html', {
        'form': form,
        'sauvegarde': sauvegarde,
        'erreurs': erreurs
    })


def read_tar(form):

    tarArchiveIO = StringIO.StringIO(form.cleaned_data["archive"].read())
    erreurs = []

    # We open the tar archive inside of the StringIO instance
    with tarfile.open(mode='r:gz', fileobj=tarArchiveIO) as tar:
        # for each EDX element belonging to the module

        try:
            xmlFile = tar.extractfile("infos.xml")
            tree = etree.parse(xmlFile)

            # Get the course infos
            cours = tree.xpath("/cours")[0]
            nom = cours.getchildren()[0].text

            # Generate the course and associate with the current user
            id_cours = id_generator()
            url_home = 'home-'+id_generator()
            cours_obj = Cours(nom_cours=nom,
                              id_cours=id_cours,
                              url_home=url_home)

            try:
                # Generate home
                homeFile = tar.extractfile("home.md")
                content = homeFile.read()
                # Prepare the string to be sent via curl to etherpad
                content = content.replace('\"', '\\\"')
                content = content.replace('`', '\\`')
                # Ask etherpad to create a new pad with the string
                os.system("curl -X POST -H 'X-PAD-ID:" +
                          url_home +
                          "' "+ETHERPAD_URL +
                          "post")
                os.system("curl -X POST --data \"" +
                          content +
                          "\" -H 'X-PAD-ID:" +
                          url_home +
                          "' " +
                          ETHERPAD_URL +
                          "post")
            except KeyError:
                erreurs.append(
                    _("Erreur de structure: home.md introuvable !"))

            # Generate each module
            cpt = 1
            modules_obj = []
            for nomMod in zip(tree.xpath("/cours/module/nomModule")):
                try:
                    moduleFile = tar.extractfile("module"+str(cpt)+".md")
                    url = 'module-'+id_generator()
                    nom_module = nomMod[0].text
                    module_obj = Module(url=url,
                                        nom_module=nom_module,
                                        cours=cours_obj)
                    modules_obj.append(module_obj)

                    content = moduleFile.read()
                    # Prepare the string to be sent via curl to etherpad
                    content = content.replace('\"', '\\\"')
                    content = content.replace('`', '\\`')
                    # Ask etherpad to create a new pad with the string
                    os.system("curl -X POST -H 'X-PAD-ID:" +
                              url +
                              "' " +
                              ETHERPAD_URL +
                              "post")
                    os.system("curl -X POST --data \"" +
                              content +
                              "\" -H 'X-PAD-ID:" +
                              url +
                              "' " +
                              ETHERPAD_URL +
                              "post")
                except KeyError:
                    erreurs.append("Erreur de structure: module" +
                                   str(cpt) +
                                   ".md introuvable !\n")
                cpt += 1

        except KeyError:
            erreurs.append("Erreur de structure: infos.xml introuvable!\n")

        tar.close()
        return cours_obj, module_obj, erreurs


def form_reupload(request):
    """
        View allowing the user to reupload a course with
        the export.tar.gz provided when generating a course
        1. Open the export.tar.gz archive
        2. Get course infos from infos.xml and create a
           Course object (generate home_url)
        3. Add the home content to a new pad
        4. For each module: Generate with module_url,
           put it into a Module object, and add the module to the course
        5. For each module: Add the module content to a new pad
        6. Link the course to the current user, and redirect to his home page.
    """

    if not request.user.is_authenticated:
        return redirect(connexion)

    profil = handle_external_user_creation(request.user)

    sauvegarde = False
    erreurs = []
    modules_obj = []

    form = ReUploadForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        cours_obj, module_obj, erreurs = read_tar(form)

        if not erreurs:
            # we can save if there's no errors
            cours_obj.save()
            profil.cours.add(cours_obj)
            profil.save()

            for module_obj in modules_obj:
                module_obj.save()

            return redirect(studio)

    return render(request, 'formreupload.html', {
        'form': form,
        'sauvegarde': sauvegarde,
        'erreurs': erreurs
    })


######################################
#                                    #
#           PREVIEW VIEWS            #
#                                    #
######################################
def apercu_module(request, id_export, feedback):
    """
        View showing the preview of a module using the culture-numerique css
        1. Get the content of the pad with urllib2
        2. Generate the module with the content
        3. parse the module in a variable
        4. render the HTML with the variable

        :param id_export: pad id
        :param feedback: do we want a feedback on the preview?
    """
    url = ETHERPAD_URL+"p/"+id_export+"/export/txt"
    response = urllib2.urlopen(url)

    feedback = feedback != "0"

    moduleData = StringIO.StringIO(response.read())
    # MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
    module = model.Module(moduleData, "module", "base")

    home_html = ''
    for sec in (module.sections):
        home_html += "\n\n<!-- Section "+sec.num+" -->\n"
        home_html += "\n\n<h1> "+sec.num+". "+sec.title+" </h1>\n"
        for sub in (sec.subsections):
            home_html += "\n\n<!-- Subsection "+sub.num+" -->\n"
            home_html += "\n\n<h2>"+sub.num+". "+sub.title+" </h2>\n"
            home_html += sub.toHTML(feedback)

    return render(request, 'apercu_module.html', {
        'res': home_html
    })


# View showing the preview of a home page using the culture-numerique css
# require the pad id
def apercu_home(request, id_export):
    """
        View showing the preview of a home page using the culture-numerique css
        1. Get the content of the pad with urllib2
        2. Simply parse the content in a variable
           (with the native python method markdown)
        3. Render the HTML with the variable

        :param id_export: pad id
    """
    url = ETHERPAD_URL+"p/"+id_export+"/export/txt"

    response = urllib2.urlopen(url)

    moduleData = response.read()
    MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
    home_html = markdown.markdown(moduleData, MARKDOWN_EXT)

    return render(request, 'apercu_home.html', {
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


def handle_external_user_creation(myUser):
    """
    For those who subscribe with django shell command (createsuperuser...)
    Create and associate a profile to the user.
    """
    try:
        profil = Profil.objects.get(user=myUser)
    except Profil.DoesNotExist:
        profil = Profil(user=myUser)
        profil.save()
    return profil


def studio(request):
    """
        View resuming the user's courses
        The user can either access an existing course, or create a new one
    """
    if not request.user.is_authenticated:
        return redirect(connexion)

    profil = handle_external_user_creation(request.user)

    form = CreateNew(request.POST or None)
    form2 = ReUploadForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        url_home = 'home-'+id_generator()
        id_cours = id_generator()
        cours = Cours(id_cours=id_cours,
                      nom_cours=form.cleaned_data['nom'],
                      url_home=url_home)
        cours.save()
        profil.cours.add(cours)

    erreurs = []
    modules_obj = []

    # form reupload
    if form2.is_valid():
        cours_obj, module_obj, erreurs = read_tar(form2)
        if not erreurs:
            # we can save if there's no errors
            cours_obj.save()
            profil.cours.add(cours_obj)
            profil.save()

            for module_obj in modules_obj:
                module_obj.save()

            return redirect(studio)

    return render(request, 'studio.html', {
        'profil': profil,
        'form': form,
        'form2': form2,
        'erreurs': erreurs
    })


def cours(request, id_cours):
    """
        View showing the information of a course.
        Possible actions:
        1. Create a new module
        2. Adding a user to the course
        3. Generating the course
            For each module belonging to the course object,
              we call urlib2 to get the content.
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
        return redirect(studio)

    # if the course doesn't belong to the user
    if not request.user.profil.cours.get(id_cours=id_cours):
        return redirect(studio)

    form_new_module = CreateNew(request.POST or None)
    form_generate = GenerateCourseForm(request.POST or None,
                                       request.FILES or None)
    form_add_user = SearchUser(request.POST or None)

    userFound = False

    # Create a new module
    if form_new_module.is_valid() and request.POST['id_form'] == '0':
        url = 'module-'+id_generator()
        nom = request.POST['nom']
        module = Module(nom_module=nom, url=url, cours=cours)
        module.save()
        cours.save()

    # Adding a user to the course
    elif form_add_user.is_valid() and request.POST['id_form'] == '1':
        user = User.objects.get(username=form_add_user.cleaned_data['user'])
        profil = user.profil
        profil.cours.add(cours)
        userFound = True

    # Generating the course
    elif form_generate.is_valid() and request.POST['id_form'] == '2':

        titleData = cours.nom_cours
        logoData = form_generate.cleaned_data["logo"]
        medias = form_generate.cleaned_data["medias"]
        feedback = form_generate.cleaned_data["feedback"]

        # url to export the pad into markdown file
        url_home = ETHERPAD_URL+'p/'+cours.url_home+'/export/txt'

        # Get the text from the etherpad instance
        # We need to create a hidden input storing
        # the plain text exporting url (of the form
        # http://<etherpad-url>/p/<pad-url>/export/txt)
        response = urllib2.urlopen(url_home)
        homeData = StringIO.StringIO(response.read())

        modulesData = []
        mediasData = []
        archiveType = "None"
        if medias:
            mediasName = form_generate.cleaned_data["medias"].name
            if re.match(r"^.*\.tar\.gz", mediasName):
                archiveType = "application/octet-stream"
            elif re.match(r"^.*\.zip", mediasName):
                archiveType = "application/zip"

        for module in cours.module_set.all():
            # get the pad content
            url_module = ETHERPAD_URL+'p/'+module.url+'/export/txt'
            response = urllib2.urlopen(url_module)
            moduleData = StringIO.StringIO(response.read())
            modulesData.append(moduleData)
        mediasData, mediasNom = cn.getMediasDataFromArchive(medias,
                                                            archiveType,
                                                            len(cours.module_set.all()))

        xmlCourse = cn.writeXMLCourse(cours)
        zip = cn.generateArchive(modulesData,
                                 mediasData,
                                 mediasNom,
                                 homeData,
                                 titleData,
                                 logoData,
                                 feedback,
                                 xmlCourse)

        response = HttpResponse(zip)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = "attachment; filename=\"site.zip\""
        return response

    cours = Cours.objects.get(id_cours=id_cours)

    return render(request, 'cours.html', {
        'cours': cours,
        'form_new_module': form_new_module,
        'form_generate': form_generate,
        'form_add_user': form_add_user,
        'userFound': userFound
    })


def module(request, id_cours, url):
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
        return redirect(studio)

    is_home = True
    name = ''
    # url starting with module: check it it belongs to the course
    # TODO: change with a parameter and avoid a regexp on the url
    if re.match(r"^module", url):
        # Check if the module exists
        try:
            module = cours.module_set.get(url=url)
        except Module.DoesNotExist:
            return redirect(studio)
        name = module.nom_module
        is_home = False

    # url starting with home: check if it is equal to the course url_home
    elif re.match(r"^home", url):
        name = "home"
        if cours.url_home != url:
            return redirect(studio)
    # the url doesn't start with "home" nor "module",
    # there is no chance it belongs to the application
    else:
        return redirect(studio)

    full_url = ETHERPAD_URL+'p/'+url

    return render(request, 'module.html', {
        'cours': cours,
        'url': url,
        'full_url': full_url,
        'name': name,
        'is_home': is_home
    })


def delete_module(request, id_cours, url):
    """
        Delete a module from a course. Irreversible task.
        (This is here we need the API_KEY,
         it is required to delete a pad from an url)

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
        return redirect(studio)

    # Check if the module exists
    try:
        module = course.module_set.get(url=url)
    except Module.DoesNotExist:
        return redirect(studio)

    # Delete the pad
    # TODO: handle errors
    urllib2.urlopen(ETHERPAD_URL +
                    "api/1/deletePad?apikey=" +
                    API_KEY +
                    "&padID=" +
                    url)
    # Delete the module model and update the course model
    module.delete()
    c = Cours.objects.get(id_cours=id_cours)
    c.save()
    return redirect(cours, id_cours=id_cours)


def delete_course(request, id_cours):
    """
        Delete a course, then redirect the user to its course list page
        Note: If a course is shared by several user,
              the course will not be deleted,
              we will just remove the ManyToManyField
              relation between the user and the course

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
    # TODO : handle errors
    urllib2.urlopen(ETHERPAD_URL +
                    "api/1/deletePad?apikey=" +
                    API_KEY +
                    "&padID=" +
                    course.url_home)

    # Only one contributor to the course: We delete it entirely.
    if len(course.profil_set.all()) == 1:
        # delete the pads belonging to the course
        for module in course.module_set.all():
            # TODO: Handle errors
            urllib2.urlopen(ETHERPAD_URL +
                            "api/1/deletePad?apikey=" +
                            API_KEY +
                            "&padID=" +
                            module.url)
            module.delete()
        course.delete()
    # More than one contributor:
    # We remove the link between the current user and the course.
    else:
        profil = request.user.profil
        course.profil_set.remove(profil)
    return redirect(studio)


#################################
#                               #
#     REPOSITORIES INTERFACE    # TODO
#                               #
#################################
def my_repositories(request):
    if not request.user.is_authenticated:
        return redirect(connexion)

    form_new_repo = CreateRepository(request.POST or None)

    myUser = request.user
    profil = Profil.objects.get(user=myUser)
    repositories = profil.repositories

    if form_new_repo.is_valid():
        git_url = form_new_repo.cleaned_data['git_url']
        default_branch = form_new_repo.cleaned_data['default_branch']
        feedback = form_new_repo.cleaned_data['feedback']

        # Check if the repository exists, create it if not
        try:
            repo = Repository.objects.get(git_url=git_url)
        except Repository.DoesNotExist:
            repo = Repository(git_url=git_url,
                              default_branch=default_branch,
                              show_feedback=feedback)
            repo.save()

        # Check if the repository belong to the user.
        try:
            profil.repositories.get(git_url=git_url)
            repo = Repository.objects.get(git_url=git_url)
        except Repository.DoesNotExist:
            profil.repositories.add(repo)

    return render(request,
                  'my_repositories.html',
                  {'repositories': repositories,
                   'user': myUser,
                   'profil': profil,
                   'form': form_new_repo})


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

    form_repo = ModifyRepository(request.POST or None,
                                 instance=repo)

    if form_repo.is_valid():
        def_branch = form_repo.cleaned_data['default_branch']
        feedbk = form_repo.cleaned_data['show_feedback']

        repo = Repository.objects.get(slug=slug)
        repo.default_branch = def_branch
        repo.show_feedback = feedbk
        repo.save()

    return render(request,
                  'repository.html',
                  {'repository': repo,
                   'form': form_repo})


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
    # More than one contributor:
    # We remove the link between the current user and the course.
    else:
        profil = request.user.profil
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

    if request.user.is_authenticated:
        return redirect(index)

    error = False
    form = ConnexionForm(request.POST or None)
        
    if form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        # check if user exists
        user = authenticate(username=username,
                            password=password)

        if user is not None:
            login(request, user)
            return redirect(index)
        else:
            error = True

    return render(request, 'connexion.html', locals())


def inscription(request):
    """
        View for creating a new user on the user side
        The form create a user (Django native class),
        and associate him to a profile, which will
        contain the user's projects
    """
    error = False
    form = CreateUserForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect(connexion)
    else:
        error = True

    return render(request, 'inscription.html', locals())


def deconnexion(request):
    """
        Disconnecting view
    """
    logout(request)
    return redirect(index)


def help(request):
    """
        markdown/gift doc view
    """
    return render(request, 'help.html')


def index(request):
    """
    The main page!
    """
    return render(request, 'index.html', {})
