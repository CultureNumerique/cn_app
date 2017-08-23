# -*- coding: utf-8 -*-
import os
import logging
import glob
import tarfile

from lxml import etree
import markdown
from io import open

import utils
from toIMS import generateIMSArchiveIO
from toEDX import generateEDXArchiveIO
import model

from zipfile import ZipFile, ZIP_DEFLATED
import StringIO

import re

from jinja2 import Environment, FileSystemLoader, Template

from cnSettings import MARKDOWN_EXT, BASE_PATH, HTML_TEMPLATES_PATH

reModuleNumber = re.compile('^module(?P<number>\d+)')
reSourceModule = re.compile('^module\d+.md$')


# ######################
# # Tools              #
# ######################
class TarReader:
    def __init__(self, archiveIO):
        self.stream = tarfile.open(mode='r:gz', fileobj=archiveIO)

    def getnames(self):
        return self.stream.getnames()

    def getStringIO(self, filename):
        element = StringIO.StringIO()
        element.write(self.stream.extractfile(filename).read())
        element.seek(0)
        return element


class ZipReader:
    def __init__(self, archiveIO):
        self.stream = ZipFile(archiveIO, 'r')

    def getnames(self):
        return self.stream.namelist()

    def getStringIO(self, filename):
        element = StringIO.StringIO()
        element.write(self.stream.read(filename))
        element.seek(0)
        return element


class ArchiveReader:
    def __init__(self,  memfile, file_type=None):
        self.modulesMap = {}
        self.moduleList = []
        self.modules_md_filenames = []
        self.modules_media_files = []
        self.modules_media_filenames = []

        archiveIO = StringIO.StringIO()
        archiveIO.write(memfile.read())
        archiveIO.seek(0)

        # We determine which type is the media archive.
        # Only two forms are accepted now: Zip and Tar.Gz
        # tar.gz has content_type application/gzip
        # In the other cases, we just skip the file
        if not file_type:
            file_type = memfile.content_type
        logging.info("Archive type : %s." % file_type)

        if file_type == "application/octet-stream":
            self.r = TarReader(archiveIO)
        elif file_type == "application/gzip":
            self.r = TarReader(archiveIO)
        elif file_type == 'application/zip':
            self.r = ZipReader(archiveIO)
        else:
            # TODO Raise an error!
            logging.exception('Archive type %s not recognized' % file_type)
            self.r = None

    def getnames(self):
        return self.r.getnames()

    def getStringIO(self, filename):
        return self.r.getStringIO(filename)

    def close(self):
        self.r.stream.close()

    def getTitle(self):
        self.title_data = self.getStringIO('title.md')
        self.title_data.seek(0)
        self.title = self.title_data.read().strip()

    def getLogo(self):
        self.logo_data = self.getStringIO('logo.png')

    def getHome(self):
        self.home_data = self.getStringIO('home.md')

    def getMetaFiles(self):
        self.getTitle()
        self.getLogo()
        self.getHome()

    def getModuleNumber(self, member):
        """Gets a module number from a filename. The number X is associated
        with any filename moduleXblah with X greater than 0. (blah can
        be anything including / etc...
        """
        res = reModuleNumber.match(member)
        if res:
            return res.group('number')
        else:
            return -1

    def getModuleFiles(self):
        """Builds a map of filenames associated with a module number. The
        method also builds a list of selected modules numbers. A
        module X is selected when the file moduleX.md is in the
        archive.
        """
        selected = {}
        for member in self.getnames():
            number = self.getModuleNumber(member)
            if number > 0:
                self.modulesMap.get(number, []).append(member)
                if not selected.get(number) and reSourceModule.match(member):
                    self.moduleList.append(number)
                    selected[number] = True
                    self.modules_md_filenames.append("module%s.md" % number)
                    self.modules_md_file_data.append(self.getStringIO(member))

    def getModulesData(self):
        """Build a list of stringIO for each markdown file associated with
        each module and a list of stringIO for each file associated
        with each module under <module>/media/*
        """
        self.getModuleFiles()
        for number in self.moduleList():
            # get all the streams associated with files matching
            # module number
            for filename in self.modulesMap.get(number):
                self.modules_media_files.append(self.getStringIO(filename))
                self.modules_media_filenames.append(filename)


#################
#    module     #
#################
def createCourseProgram(moduleFiles, title, feedback):

    course_program = model.CourseProgram(title, '')

    i = 1
    for moduleFile in moduleFiles:
        # The only way I could find to encode
        # InMemoryUploadedFile into utf-8 (avoid warning)
        # moduleFileEnc = TextIOWrapper(moduleFile, encoding='utf-8')
        moduleFile.seek(0)
        m = model.Module(moduleFile, "module"+str(i), '')
        m.toHTML(feedback)
        i = i+1
        course_program.modules.append(m)

    return course_program


def addFolderToZip(myZipFile, folder_src, folder_dst):
    """
        Add an entire folder to a zip file

        Adding an entire folder to a zip file
        (used to copy the static folder into the zipfile)

        :param myZipFile: zip where we add the folder (StringIO)
        :param folder_src: path from where we want to get the
                           folder (String)
        :param folder_dst: path in the zipfile where to copy the
                           folder (String)
    """
    # convert path to ascii for ZipFile Method
    folder_src = folder_src.encode('ascii')
    for file in glob.glob(folder_src+"/*"):
        if os.path.isfile(file):
            myZipFile.write(file, folder_dst+os.path.basename(file),
                            ZIP_DEFLATED)
        elif os.path.isdir(file):
            addFolderToZip(myZipFile, file,
                           folder_dst+os.path.basename(file)+'/')


# FIXME: is it a duplicate of extractMediaArchive?
def getMediasDataFromArchive(medias_archive, medias_type, nb_modules):
    """
        Go through a tar.gz/zip archive and get the medias associated with
        each modules from a tar.gz archive

        Archive structure:
          Medias associated with moduleX are in a directory moduleX
          (examples: module1, module3, module4, module6...)

        returns mediasData, which is a list of lists,
        each module is a list, containing a list of StringIO data

        returns mediasNames, which is a list of lists,
        each module is a list, containing a set of names (String)


        :param medias_archive: InMemoryUploadedFile (either zip or tar.gz),
                containing the different medias in folders.
        :param medias_type: String determining the archive type,
                either "application/octet-stream" or "application/zip"
        :param nb_modules: number of module in the course
        :return: A couple of StringIO lists, mediasData and mediasNom,
                 containing the media data and medias name
    """

    mediasData = []
    mediasNames = []

    # no archive given, return a list of empty lists
    if not medias_archive:
        for i in range(1, int(nb_modules) + 1):
            mediasData.append([])
            mediasNames.append([])
        return mediasData, mediasNames

    # get a reader depending on the archive type
    reader = ArchiveReader(medias_archive, medias_type)

    # go through the archive files and create
    # the StringIO containing modules and medias
    for i in range(1, int(nb_modules) + 1):
        mediaData = []
        mediaName = []
        reModuleData = re.compile('^module'+str(i)+'/(?P<nom>.*)$')
        for member in reader.getNames():
            res = reModuleData.match(member)
            if res:
                media = reader.getStringIO(member)
                mediaData.append(media)
                mediaName.append(res.groupdict()['nom'])
                mediasData.append(mediaData)
                mediasNames.append(mediaName)

        reader.close()

    return mediasData, mediasNames


def writeXMLCourse(course_program):
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
    nom.text = course_program.title

    for module in course_program.modules:
        moduleXML = etree.SubElement(coursXML, "module")
        nomModule = etree.SubElement(moduleXML, "nomModule")
        nomModule.text = module.name

    return etree.tostring(coursXML, pretty_print=True)


def createExportArchive(zipFile,
                        base_arc_name,
                        course_program,
                        modulesData,
                        homeFile,
                        archive_included=False):
    """Packs the markdown files and xml file into the zipFile archive and
       also prepares an archive file for further import facilities (if
       archive_included is True

       :param zipFile: zipfile where to add the export archive (StringIO)

       :param base_arc_name: base directory in the archive zipFile

       :archive_included: if True adds an archive in the archive for
       an easiest import

       :return: the actualized zipfile

    """
    if archive_included:
        inc_archiveIO = StringIO.StringIO()
        # inc_archive = tarfile.open(mode='w:gz', fileobj=inc_archiveIO)
        inc_archive = ZipFile(inc_archiveIO, 'w')

    # XML
    xml = writeXMLCourse(course_program)
    zipFile.writestr(os.path.join(base_arc_name,
                                  "export",
                                  "infos.xml"),
                     xml)

    # write into the archive the different md files
    if homeFile is not None:
        homeFile.seek(0)
        homeContent = homeFile.read()
        zipFile.writestr(os.path.join(base_arc_name,
                                      'export',
                                      'home.md'),
                         homeContent)
    if archive_included:
        inc_archive.writestr(os.path.join(base_arc_name,
                                          "export",
                                          "infos.ml"),
                             xml)
        if homeFile is not None:
            inc_archive.writestr(os.path.join(base_arc_name,
                                              'export',
                                              'home.md'),
                                 homeContent)
    i = 1
    for moduleData in modulesData:
        moduleContent = moduleData.read()
        zipFile.writestr(os.path.join(base_arc_name,
                                      'export',
                                      'module'+str(i)+'.md'),
                         moduleContent)
        if archive_included:
            inc_archive.writestr(os.path.join(base_arc_name,
                                              'export',
                                              'module'+str(i)+'.md'),
                                 moduleContent)
        i = i+1

    if archive_included:
        inc_archive.close()
        inc_archiveIO.seek(0)
        zipFile.writestr(os.path.join(base_arc_name,
                                      "export.zip"),
                         inc_archiveIO.read())

    return zipFile


def get_templates(siteTemplate=None,
                  indexTemplate=None,
                  moduleTemplate=None):
    """ prepare HTML templates"""
    if siteTemplate is None:
        jenv = Environment(loader=FileSystemLoader(HTML_TEMPLATES_PATH))
        jenv.filters['slugify'] = utils.cnslugify
        site_template = jenv.get_template("site_layout.tmpl")
    else:
        site_template = Template(siteTemplate.read())

    if moduleTemplate is None:
        module_template = jenv.get_template("module.html")
    else:
        module_template = Template(moduleTemplate.read())

    if indexTemplate is None:
        index_template = jenv.get_template("index.tmpl")
    else:
        index_template = Template(indexTemplate.read())

    return site_template, module_template, index_template


def extractMediaArchive(mediaArchiveFiles, course_program):
    """Extract medias contained in a tar.gz or a zip archive. If the top
    level directory in the archive is media, then the names are just the
    path suffixes.

    used in form_upload, when the user gives an archive of medias for
    one module.

    returns a couple containing a list of each files of each modules
    (StringIO), and their names.

    returns moduleMediaFiles, which is a 2 dimensional list, each
    member is a list, containing a set of files (StringIO data)

    returns moduleMediaNames, which is a 2 dimensional list, each
    member is a list, containing a set of name (String)

    :param mediaArchiveFiles: set of archive containing medias file
    :return: moduleMediaFiles, moduleMediaNames

    """
    moduleMediaFiles = []
    moduleMediaNames = []

    # one iteration correspond to one module
    # We want to extract all the files in StringIO iterations
    i = 0
    for mediaArchiveFile in mediaArchiveFiles:
        mediaFiles = []
        mediaNames = []
        if mediaArchiveFile is not None:
            r = ArchiveReader(mediaArchiveFile)

            for member in r.getnames():
                name = re.sub('^media/', '', member)
                if name == "media":  # skip the toplevel dir
                    continue
                if name.startswith('logo.'):
                    course_program.modules[i].logo_filename = os.path.join(
                        course_program.modules[i].name,
                        'media',
                        name)
                media = r.getStringIO(member)
                mediaFiles.append(media)
                mediaNames.append(name)
            r.close()

        moduleMediaFiles.append(mediaFiles)
        moduleMediaNames.append(mediaNames)
        i += 1

    return moduleMediaFiles, moduleMediaNames


def createSiteArchive(course_program,
                      modulesData,
                      mediaFiles,
                      mediaNames,
                      homeFile,
                      logoFile,
                      siteTemplate=None,
                      moduleTemplate=None,
                      indexTemplate=None):
    """
        Build the site and return the archive,
        used in every part of the app generating course archive

        We need the course object and the different datas to use this fonction.
        1. Write infos.xml, logo.png, title, index.
        2. Then loop into each module to generate the EDX, the IMSCC, and HTML.
        3. Copy the md file and then create the export archive.

        :param course_program: Course program to generate info.xml
        :param modulesData: module datas to copy in the archive (StringIO list)
        :param mediaFiles: media datas to copy in the archive (StringIO list)
        :param mediasNames: media names to keep when we copy it (String list)
        :param homeFile: home data to copy in the archive (StringIO)
        :param title: title of the course (String)
        :param logoFile: logo.png data (StringIO)
        :param xmlCourse: xml course for putting into the export archive

        :return: the entire zipfile containing the course
    """
    # FIXME: check for invalid characters
    base_arc_name = course_program.title

    inMemoryOutputFile = StringIO.StringIO()
    zipFile = ZipFile(inMemoryOutputFile, 'w')

    # Add static directory in the archive
    addFolderToZip(zipFile, BASE_PATH+'/static/',
                   os.path.join(base_arc_name, 'static/'))

    site_template, module_template, index_template = get_templates(
        siteTemplate, moduleTemplate, indexTemplate)

    # LOGO
    # if found, copy logo.png, else use default
    if logoFile is not None:
        root, ext = os.path.splitext(logoFile.name)
        logoFilename = "logo." + ext
        zipFile.writestr(os.path.join(base_arc_name, logoFilename),
                         logoFile.read())
    else:  # the 'default' value denotes the default logo in the template
        logoFilename = 'default'

    # INDEX
    if homeFile is None:
        with open(os.path.join(HTML_TEMPLATES_PATH, 'default_home.html'),
                  'r', encoding='utf-8') as f:
            home_html = f.read()
    else:
        try:
            home_html = markdown.markdown(homeFile.read(), MARKDOWN_EXT)
        except Exception as err:
            # use default from template
            logging.error(" Cannot parse home markdown ")
            home_html = ""

    # INDEX
    # write index.html file
    index_content = index_template.render(course=course_program,
                                          index_content=home_html)
    index_html = site_template.render(course=course_program,
                                      content=index_content,
                                      body_class="home",
                                      logo=logoFilename)

    zipFile.writestr(os.path.join(base_arc_name, 'index.html'),
                     index_html.encode("UTF-8"))

    # MODULE
    # Loop through modules
    for module, moduleMediaFiles, moduleMediaNames in zip(course_program.modules,
                                                          mediaFiles,
                                                          mediaNames):
        imsfileIO = generateIMSArchiveIO(module,
                                         moduleMediaFiles,
                                         moduleMediaNames)
        imsfileIO.seek(0)
        zipFile.writestr(os.path.join(base_arc_name,
                                      module.name + '_imscc.zip'),
                         imsfileIO.read())
        edxfileIO = generateEDXArchiveIO(module,
                                         moduleMediaFiles,
                                         moduleMediaNames)
        edxfileIO.seek(0)
        zipFile.writestr(os.path.join(base_arc_name,
                                      module.name + '_edx.tar.gz'),
                         edxfileIO.read())

        # write html, XML files
        if moduleMediaFiles:
            for mediaFile, filename in zip(moduleMediaFiles, moduleMediaNames):
                mediaFile.seek(0)
                zipFile.writestr(os.path.join(base_arc_name,
                                              module.name,
                                              'media',
                                              filename),
                                 mediaFile.read())

        zipFile.writestr(os.path.join(base_arc_name,
                                      module.name,
                                      module.name +
                                      '.questions_bank.gift.txt'),
                         module.toGift().encode("UTF-8"))
        zipFile.writestr(os.path.join(base_arc_name,
                                      module.name,
                                      module.name +
                                      '.video_iframe_list.txt'),
                         module.toVideoList().encode("UTF-8"))
        module_html_content = module_template.render(module=module)
        html = site_template.render(course=course_program,
                                    content=module_html_content,
                                    body_class="modules",
                                    logo=logoFilename)

        # change the absolute path into a relative path.
        # We just need to add . to create the relative path.

        # FIXME : We should deal with the image link in another way...
        # Essayer: Module(ModuleData, 'nom_module', '')
        # au lieu de Module(ModuleData, 'nom_module')
        absoluteMedia = re.compile(r"/module(?P<num_module>[0-9]+)/media")
        toRelative = r"./module\g<num_module>/media"
        html = re.sub(absoluteMedia, toRelative, html)
        zipFile.writestr(os.path.join(base_arc_name,
                                      module.name+'.html'),
                         html.encode("UTF-8"))

    # create export files and archive
    zipFile = createExportArchive(zipFile,
                                  base_arc_name,
                                  course_program,
                                  modulesData,
                                  homeFile,
                                  archive_included=True)

    zipFile.close()
    inMemoryOutputFile.seek(0)

    return inMemoryOutputFile


# ###########################
# functions called from views
# ###########################
def generateSiteArchive(moduleFiles,
                        mediaArchiveFiles,
                        homeFile,
                        title,
                        logoFile,
                        feedback,
                        siteTemplate=None,
                        moduleTemplate=None):
    """
        Generate an archive from a set of data.

        1. we process the set of moduleFiles into Module objects
        2. we create the course objects
        3. we call createSiteArchive which will create the archive
        4. we return the zipfile created.

        :param moduleFiles: list of modules data (list of StringIO)
        :param mediaArchiveFiles: list of medias Archives (UploadedFile)
        :param title: title of the cours
        :param logoFile: logo of the course
        :param feedback: feedback on the course

        :return: zip file containing the course.

    """
    course_program = createCourseProgram(moduleFiles, title, feedback)

    # get Medias associated with modules
    # logo for modules can appear in this archive, we need the course_program.
    mediaFiles, mediaNames = extractMediaArchive(mediaArchiveFiles,
                                                 course_program)

    return createSiteArchive(course_program,
                             moduleFiles,
                             mediaFiles,
                             mediaNames,
                             homeFile,
                             logoFile,
                             siteTemplate,
                             moduleTemplate)


def generateSiteArchiveFromArchive(title, archiveData, archiveType, feedback):
    """Generate the site archive from an entire archive which followed the
        repository model established before.  Uses tar.gz

        1. Open the tar archive into a StringIO instance
           (no memory manipulation on the disk)
        2. Go through the archive files and create the
           StringIO containing modules and medias
        3. Generate the course with the buildSiteLight method.

        :param archiveData: InMemoryUploadedFile containing
                            a tar.gz archiveData
        :param feedback: do we want a feedback on the HTML website generated?
        :return: zipfile containing the course generated, erreurs containing a
                 list of string errors, and the title in a string

    """
    erreurs = []
    r = ArchiveReader(archiveData, archiveType)
    # Read the modules, etc in the provided archive
    r.getMetaFiles()  # get title, home, logo
    r.getModulesData()  # get source, and media data and names
    r.close()
    course_program = createCourseProgram(r.modules_md_file_data,
                                         title,
                                         feedback)
    archive = createSiteArchive(course_program,
                                r.modules_md_filenames,
                                r.modules_media_files,
                                r.modules_media_filenames,
                                r.home_data,
                                r.logo_data)

    return archive, r.title, erreurs
