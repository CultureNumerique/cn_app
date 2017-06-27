# -*- coding: utf-8 -*-
import os
import logging
import glob
import tarfile

from lxml import etree
import markdown
from io import open

import utils
import toIMS
import toEDX
import model

import zipfile
from zipfile import ZipFile
import StringIO
import re

from jinja2 import Environment, FileSystemLoader

MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TEMPLATES_PATH = os.path.join(BASE_PATH, 'templates')
LOGFILE = 'logs/cnExport.log'


#################
#    module     #
#################
def processModuleLight(moduleName, moduleData, feedback):
    """
        Create a module

        We create a Module object, we add its name,
        and depending on the feedback parameter,
        we will parse the module to HTML with feedback or not.

        :param moduleName: The module name (String)
        :param moduleData: The module data (StringIO)
        :param feedback: Do we want feedback on the HTML generated? (Boolean)

        :return: The Module object
    """

    m = model.Module(moduleData, moduleName, '')
    m.toHTML(feedback)  # only generate html for all subsections

    return m


#####################
#     course_obj    #
#####################
def processRepositoryLight(modules):
    """
        Create the course object

        We create a Course object and we add the different module object to it.

        :param modules: The first number to add
        :return: The Course object
    """
    course_obj = model.CourseProgram('')

    for module in modules:
        course_obj.modules.append(module)
    return course_obj


def addFolderToZip(myZipFile, folder_src, folder_dst):
    """
        Add an entire folder to a zip file

        Adding an entire folder to a zip file
        (used to copy the static folder into the zipfile)

        :param myZipFile: zip where we add the folder (StringIO)
        :param folder_src: path from where we want to get the folder (String)
        :param folder_dst: path in the zipfile where to copy the folder (String)
    """
    # convert path to ascii for ZipFile Method
    folder_src = folder_src.encode('ascii')
    for file in glob.glob(folder_src+"/*"):
        if os.path.isfile(file):
            myZipFile.write(file, folder_dst+os.path.basename(file),
                            zipfile.ZIP_DEFLATED)
        elif os.path.isdir(file):
            addFolderToZip(myZipFile, file,
                           folder_dst+os.path.basename(file)+'/')


def getMediasDataFromArchive(medias_archive, medias_type, nb_module, ):
    """
        Get all the medias from each modules from a tar.gz archive

        Go through a tar.gz/zip archive, get all the medias from each modules
        In the archive, there must be a folder for each module containing files
        (exemple: module1,module3,module4,module6...)
        We store every medias and names into mediasData and mediasNom.

        returns mediasData, which is a 2 dimensional list,
        each module is a list, containing a set of StringIO data

        returns mediasNom, which is a 2 dimensional list,
        each module is a list, containing a set of name (String)


        :param medias: MemoryUploadedFile (either zip or tar.gz),
                containing the different medias in folders.
        :param medias_type: String determining the archive type,
                either "application/octet-stream" or "application/zip"
        :param nb_module: number of module in the course
        :return: A couple of StringIO list, mediasData and mediasNom,
                 containing the media data and medias name
    """

    mediasData = []
    mediasNom = []

    if not medias_archive:
        for i in range(1, int(nb_module) + 1):
            mediasData.append([])
            mediasNom.append([])
        return mediasData, mediasNom

    if medias_type == "application/octet-stream":
        tarArchiveIO = StringIO.StringIO()
        tarArchiveIO.write(medias_archive.read())
        tarArchiveIO.seek(0)

        # We open the tar archive inside of the StringIO instance
        with tarfile.open(mode='r:gz', fileobj=tarArchiveIO) as tar:

            # go through the archive files and create
            # the StringIO containing modules and medias
            for i in range(1, int(nb_module) + 1):
                mediaData = []
                mediaNom = []
                reModuleData = re.compile('^module'+str(i)+'/(?P<nom>.*)$')
                for member in tar.getnames():
                    res = reModuleData.match(member)
                    if res:
                        media = StringIO.StringIO()
                        media.write(tar.extractfile(member).read())
                        media.seek(0)
                        mediaData.append(media)
                        mediaNom.append(res.groupdict()['nom'])
                mediasData.append(mediaData)
                mediasNom.append(mediaNom)

        tar.close()

    elif medias_type == "application/zip":
        zipArchiveIO = StringIO.StringIO()
        zipArchiveIO.write(medias_archive.read())
        zipArchiveIO.seek(0)
        with ZipFile(zipArchiveIO, 'r') as zipfile:

            for i in range(1, int(nb_module) + 1):
                mediaData = []
                mediaNom = []
                reModuleData = re.compile('^module'+str(i)+'/(?P<nom>.*)$')
                for member in zipfile.namelist():
                    res = reModuleData.match(member)
                    if res:
                        media = StringIO.StringIO()
                        media.write(zipfile.read(member))
                        media.seek(0)
                        mediaData.append(media)
                        mediaNom.append(res.groupdict()['nom'])
                mediasData.append(mediaData)
                mediasNom.append(mediaNom)

            zipfile.close()

    return mediasData, mediasNom


def writeXMLCourse(cours):
    """
        Write a XML file in string from a Cours Model
        (used for importing later)

        Structure of the xml:
        <cours>
            <nom>Nom du cours</nom>
            <nbModule>2</nbModule>
            <module>
                <nomModule>module 1</nomModule>
                <nomModule>module 2</nomModule>
            </module>
        </cours>

        :param cours: the Course object
        :return: the actualized zipfile
    """
    coursXML = etree.Element("cours")
    nom = etree.SubElement(coursXML, "nom")
    nom.text = cours.nom_cours
    #nbModule = etree.SubElement(coursXML, "nbModule")
    #nbModule.text = str(cours.nb_module)

    for module in cours.module_set.all():
        moduleXML = etree.SubElement(coursXML, "module")
        nomModule = etree.SubElement(moduleXML, "nomModule")
        nomModule.text = module.nom_module

    return etree.tostring(coursXML, pretty_print=True)


def createExportArchive(zipFile):
    """
        Pack the markdown files and xml file into a tar archive.

        Pack the markdown files and xml file into a tar archive.
        the user may use it again later for reuploading his course.

        :param myZipFile: zipfile where to add the export archive (StringIO)
        :return: the actualized zipfile
    """
    # pack it up into a tar archive
    # by using regex to determine which file must be included in that archive
    # (We have to look into the archive being generated)
    tab = zipFile.namelist()
    reExportPath = re.compile('^export/')

    tarArchiveIO = StringIO.StringIO()

    # We open the tar archive inside of the StringIO instance
    with tarfile.open(mode='w:gz', fileobj=tarArchiveIO) as tar:
        # for each EDX element belonging to the module
        for elt in tab:
            res = reExportPath.match(elt)

            if res:
                # adding the file to the tar archive
                # (we need tarInfo and StringIO instance
                # for not writing anything on the disk)
                path = elt.replace('export/', '')
                data = zipFile.read(elt)
                info = tarfile.TarInfo(name=path)
                info.size = len(data)
                tar.addfile(tarinfo=info, fileobj=StringIO.StringIO(data))
        tar.close()

    tarArchiveIO.seek(0)
    zipFile.writestr("export/export.tar.gz", tarArchiveIO.read())

    return zipFile


def buildSiteLight(course_obj, modulesData,
                   mediasData, mediasNom,
                   homeData, titleData,
                   logoData, xmlCourse):
    """
        Build the site and return the archive,
        used in every part of the app generating course archive

        We need the course object and the different datas to use this fonction.
        1. Write infos.xml, logo.png, title, index.
        2. Then loop into each module to generate the EDX, the IMSCC, and HTML.
        3. Copy the md file and then create the export archive.

        :param course_obj: Course object -> for parsing
        :param modulesData: module datas -> to copy in the archive (StringIO list)
        :param mediasData: media datas -> to copy in the archive (StringIO list)
        :param mediasNom: media names -> to keep the name of medias when we copy it (String list)
        :param homeData: home data -> to copy in the archive (StringIO)
        :param titleData: title of the course (String)
        :param logoData: logo.png data (StringIO)
        :param xmlCourse: xml course for putting into the export archive

        :return: the entire zipfile containing the course
    """

    inMemoryOutputFile = StringIO.StringIO()
    zipFile = ZipFile(inMemoryOutputFile, 'w')
    addFolderToZip(zipFile, BASE_PATH+'/static/', 'static/')

    jenv = Environment(loader=FileSystemLoader(TEMPLATES_PATH))
    jenv.filters['slugify'] = utils.cnslugify
    site_template = jenv.get_template("site_layout.html")

    # XML
    zipFile.writestr("export/infos.xml", xmlCourse)

    # LOGO
    # if found, copy logo.png, else use default
    logo_files = logoData
    if logoData is not None:
        logo = "logo.png"
        zipFile.writestr(logo, logo_files.read())
    else:  # use default one set in template
        logo = 'default'

    # TITLE
    course_obj.title = titleData

    # INDEX
    custom_home = False
    try:
        f = homeData
        home_data = f.read()
        home_html = markdown.markdown(home_data, MARKDOWN_EXT)
        custom_home = True

    except Exception as err:
        # use default from template
        logging.error(" Cannot parse home markdown ")
        with open(os.path.join(TEMPLATES_PATH, 'default_home.html'),
                  'r', encoding='utf-8') as f:
            home_html = f.read()

    # INDEX
    # write index.html file
    html = site_template.render(course=course_obj,
                                module_content=home_html,
                                body_class="home",
                                logo=logo,
                                custom_home=custom_home)
    zipFile.writestr('index.html', html.encode("UTF-8"))


    ####MODULE
    # Loop through modules
    for module, mediaData, mediaNom in zip(course_obj.modules,
                                           mediasData,
                                           mediasNom):
        zipFile = toEDX.generateEDXArchiveLight(module, module.module, zipFile)
        zipFile = toIMS.generateImsArchiveLight(module, module.module, zipFile)

        # write html, XML, and JSon files
        file_path = module.module

        if mediaData:
            for media, nom in zip(mediaData, mediaNom):
                zipFile.writestr(file_path+'/media/'+nom, media.read())

        zipFile.writestr(file_path+'/'+module.module+'.questions_bank.gift.txt',
                         module.toGift().encode("UTF-8"))
        zipFile.writestr(file_path+'/'+module.module+'.video_iframe_list.txt',
                         module.toVideoList().encode("UTF-8"))
        # FIXME : this file should be optionnaly written
        # mod_config = zipFile.writestr(file_path+'/'+module.module+'.config.json',
        #                              module.toJson().encode("UTF-8"))

        module_template = jenv.get_template("module.html")
        module_html_content = module_template.render(module=module)
        html = site_template.render(course=course_obj,
                                    module_content=module_html_content,
                                    body_class="modules",
                                    logo=logo)

        # change the absolute path into a relative path.
        # On the first app:
        # <img alt="hiragana" src="http://escapad.univ-lille3.fr/data/sites/github-com_lmagniez_course_template/module2/media/hira.gif">
        # When we generate on the new app:
        # <img alt="hiragana" src="/module2/media/hira.gif">
        # We just need to add . to create the relative path.

        absoluteMedia = re.compile(r"/module(?P<num_module>[0-9]+)/media")
        toRelative = r"./module\g<num_module>/media"
        html = re.sub(absoluteMedia, toRelative, html)
        zipFile.writestr(module.module+'.html', html.encode("UTF-8"))

    # write into the archive the different md files
    homeData.seek(0)
    zipFile.writestr('export/home.md', homeData.read())
    i = 1
    for moduleData in modulesData:
        zipFile.writestr('export/module'+str(i)+'.md', moduleData.read())
        i = i+1

    # create export archive
    zipFile = createExportArchive(zipFile)

    zipFile.close()
    inMemoryOutputFile.seek(0)

    return inMemoryOutputFile


def generateArchive(modulesData,
                    mediasData,
                    mediasNom,
                    homeData,
                    titleData,
                    logoData,
                    feedback,
                    xmlCourse=""):
    """
        Generate an archive from a set of data.

        1. we process the set of moduleData into Module objects
        2. we create the course objects
        3. we call buildSiteLight which will create the archive
        4. we return the zipfile created.

        :param modulesData: list of modules data (list of StringIO)
        :param mediasData: list of medias data (list of StringIO)
        :param mediasNom: list of medias name (list of String)
        :param titleData: title of the cours
        :param logoData: logo of the course
        :param feedback: feedback on the course
        :param xmlCourse: xml file for importing the course later into the app.

        :return: zip file containing the course.

    """
    modules = []
    i = 1
    for moduleData in modulesData:
        # The only way I could find to encode
        # InMemoryUploadedFile into utf-8 (avoid warning)
        # moduleData = TextIOWrapper(moduleData.file, encoding='utf-8')
        m = processModuleLight("module"+str(i), moduleData, feedback)
        modules.append(m)
        moduleData.seek(0)
        i = i+1
    c = processRepositoryLight(modules)

    outputFile = buildSiteLight(c, modulesData, mediasData,
                                mediasNom, homeData, titleData,
                                logoData, xmlCourse)

    return outputFile


def extractMediaArchive(mediasData, mediasType):
    """extract the different medias contained in a tar.gz or a zip archive

    used in form_upload, when the user give tar.gz archive media for
    each module.

    returns a couple containing a list of each files of each modules
    (StringIO), and their names.

    returns mediasDataObj, which is a 2 dimensional list, each module
    is a list, containing a set of StringIO data

    returns mediasNom, which is a 2 dimensional list, each module is a
    list, containing a set of name (String)

    :param mediasData: set of archive containing medias file (list of InMemoryUploadedFile)
    :param mediasType: String list -> None or application/octet-stream
    :return: mediasDataObj mediasNom

    """
    mediasDataObj = []
    mediasNom = []

    # one iteration correspond to one module
    # We want to extract all the files in StringIO iterations
    for mediaData, mediaType in zip(mediasData, mediasType):
        mediaDataObj = []
        mediaNom = []

        # We determine which type is the media archive.
        # Only two forms are accepted now: Zip and Tar.Gz
        # In the other cases, we just skip the file

        # Dealing with tar.gz archive
        if mediaType == 'application/octet-stream':
            tarArchiveIO = StringIO.StringIO()
            tarArchiveIO.write(mediaData.read())
            tarArchiveIO.seek(0)

            # We open the tar archive inside of the StringIO instance
            with tarfile.open(mode='r:gz', fileobj=tarArchiveIO) as tar:
                for member in tar.getnames():
                    media = StringIO.StringIO()
                    media.write(tar.extractfile(member).read())
                    media.seek(0)
                    mediaDataObj.append(media)
                    mediaNom.append(member)
                tar.close()
            mediasDataObj.append(mediaDataObj)
            mediasNom.append(mediaNom)

        # Dealing with zip archive
        elif mediaType == 'application/zip':
            zipArchiveIO = StringIO.StringIO()
            zipArchiveIO.write(mediaData.read())
            zipArchiveIO.seek(0)
            with ZipFile(zipArchiveIO, 'r') as zipfile:
                for member in zipfile.namelist():
                    media = StringIO.StringIO()
                    media.write(zipfile.read(member))
                    media.seek(0)
                    mediaDataObj.append(media)
                    mediaNom.append(member)
                zipfile.close()

            mediasDataObj.append(mediaDataObj)
            mediasNom.append(mediaNom)

        # Default case: Nothing is done here
        else:
            mediasDataObj.append(None)
            mediasNom.append(None)

    return mediasDataObj, mediasNom


def StringIOFromTarFile(tarFile, nomFichier):
    """
        Get a file within a tarfile object and convert it
        into a StringIO object

        :param tarFile: tarfile (StringIO)
        :param nomFichier: filename (String)
        :return: StringIO containing the file from the tarfile

    """
    element = StringIO.StringIO()
    element.write(tarFile.extractfile(nomFichier).read())
    element.seek(0)
    return element


def StringIOFromZipFile(zipFile, nomFichier):
    """
        Get a file within a zipfile object and convert it
        into a StringIO object

        :param zipFile: zipfile (StringIO)
        :param nomFichier: filename (String)
        :return: StringIO containing the file from the tarfile

    """
    element = StringIO.StringIO()
    element.write(zipFile.read(nomFichier))
    element.seek(0)
    return element


def generateArchiveLight(archiveData, archiveType, feedback):
    """Generate the archive with an entire archive which followed the
        repository model established before.  Uses tar.gz

        1. Open the tar archive into a StringIO instance
           (no memory manipulation on the disk)
        2. Go through the archive files and create the
           StringIO containing modules and medias
        3. Generate the course with the buildSiteLight method.

        :param archiveData: InMemoryUploadedFile containing a tar.gz archiveData
        :param feedback: do we want a feedback on the HTML website generated?
        :return: zipfile containing the course generated, erreurs containing list of string errors, and the title in a string

    """
    modulesData = []
    mediasData = []
    mediasNom = []
    erreurs = []
    titleData = ''

    if archiveType == "application/octet-stream":

        tarArchiveIO = StringIO.StringIO()
        tarArchiveIO.write(archiveData.read())
        tarArchiveIO.seek(0)

        homeData = StringIO.StringIO()

        # We open the tar archive inside of the StringIO instance
        with tarfile.open(mode='r:gz', fileobj=tarArchiveIO) as tar:

            try:
                titleData = StringIOFromTarFile(tar, 'title.md')
            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver title.md !")
            try:
                homeData=StringIOFromTarFile(tar, 'home.md')
            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver home.md !")
            try:
                logoData=StringIOFromTarFile(tar, 'logo.png')
            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver logo.png !")

            res = True
            maxModule = -1
            reModule = re.compile('^module(?P<cptModule>\d)')

            # search for the number of modules in the archive
            for member in tar.getnames():
                res = reModule.match(member)
                if(res):
                    nbModule = res.groupdict()['cptModule']
                    if maxModule < nbModule:
                        maxModule = nbModule

            # go through the archive files and create
            # the StringIO containing modules and medias
            for i in range(1, int(maxModule) + 1):
                reModuleData = re.compile('^module'+str(i)+'/.*\.md$')
                reMediaData = re.compile('^module'+str(i)+'/media/(?P<nom>.*)$')
                mediaData = []
                nomData = []
                oneModuleFound = False
                for member in tar.getnames():
                    res = reModuleData.match(member)
                    if res and not oneModuleFound:
                        module = StringIOFromTarFile(tar, member)
                        modulesData.append(module)
                        oneModuleFound = True
                    res = reMediaData.match(member)
                    if(res):
                        media = StringIOFromTarFile(tar, member)
                        mediaData.append(media)
                        nomData.append(res.groupdict()['nom'])
                if not oneModuleFound:
                    erreurs.append("Il manque le module "+str(i)+" !")
                mediasData.append(mediaData)
                mediasNom.append(nomData)

            tar.close()

    # Zip case
    elif archiveType == "application/zip":
        zipArchiveIO = StringIO.StringIO()
        zipArchiveIO.write(archiveData.read())
        zipArchiveIO.seek(0)



        homeData = StringIO.StringIO()

        # We open the tar archive inside of the StringIO instance
        with ZipFile(zipArchiveIO, 'r') as zipfile:
            try:
                titleData = StringIOFromZipFile(zipfile, 'title.md')
                #titleData = tar.extractfile('title.md').read()
            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver title.md !");
            try:
                homeData = StringIOFromZipFile(zipfile, 'home.md')
            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver home.md !");
            try:
                logoData = StringIOFromZipFile(zipfile, 'logo.png')
            except KeyError:
                erreurs.append("Erreur de structure: Impossible de trouver logo.png !");

            res = True
            maxModule = -1
            reModule = re.compile('^module(?P<cptModule>\d)')

            # search for the number of modules in the archive
            for member in zipfile.namelist():
                res = reModule.match(member)
                if(res):
                    nbModule = res.groupdict()['cptModule']
                    if maxModule < nbModule:
                        maxModule = nbModule

            # go through the archive files and create
            # the StringIO containing modules and medias
            for i in range(1, int(maxModule) + 1):
                reModuleData = re.compile('^module'+str(i)+'/.*\.md$')
                reMediaData = re.compile('^module'+str(i)+'/media/(?P<nom>.*)$')
                mediaData = []
                nomData = []
                oneModuleFound = False
                for member in zipfile.namelist():
                    res = reModuleData.match(member)
                    if res and not oneModuleFound:
                        module = StringIOFromZipFile(zipfile, member)
                        modulesData.append(module)
                        oneModuleFound = True
                    res = reMediaData.match(member)
                    if(res):
                        media = StringIOFromZipFile(zipfile, member)
                        mediaData.append(media)
                        nomData.append(res.groupdict()['nom'])
                if not oneModuleFound:
                    erreurs.append("Il manque le module "+str(i)+" !")
                mediasData.append(mediaData)
                mediasNom.append(nomData)

            zipfile.close()

    modules = []
    i = 1
    for moduleData in modulesData:
        # The only way I could find to encode
        # InMemoryUploadedFile into utf-8 (avoid warning)
        # moduleData = TextIOWrapper(moduleData.read(), encoding='utf-8')
        m = processModuleLight("module"+str(i), moduleData, feedback)
        modules.append(m)
        i = i+1
    c = processRepositoryLight(modules)

    outputFile = ""
    if not erreurs:
        outputFile = buildSiteLight(c, modulesData, mediasData,
                                    mediasNom, homeData,
                                    titleData.read(), logoData, '')

    # Process the title data into a 1 line string, in order to give the name to the archive.
    titleData.seek(0)
    title = titleData.read()
    title = re.sub(r"\n", r"", title)

    return outputFile, title ,erreurs
