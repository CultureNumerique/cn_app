#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import logging
import shutil
import glob
import tarfile

from lxml import etree
from lxml import html
import markdown
from lxml.html.clean import Cleaner
from io import open
from jinja2 import Template, Environment, FileSystemLoader

import utils
import model
import fromGift
import re
import StringIO
from tarfile import TarFile



MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
EDX_TEMPLATES_PATH = os.path.join(BASE_PATH, 'templates', 'toEDX' )
EDX_DEFAULT_FILES = {
    'about':'overview.html',
    'assets':'assets.xml',
    'info':'updates.html',
    'policies':'assets.json'
}
EDX_ADVANCED_MODULE_LIST = ['cnvideo', 'library_content']
EDX_GRADER_MAP = {
    'Activite':'Activite',
    'ActiviteAvancee':'Activite Avancee',
    'Comprehension':'Comprehension',
    'webcontent': None,
}

def loadJinjaEnv():
    jenv = Environment(loader=FileSystemLoader(EDX_TEMPLATES_PATH))
    jenv.filters['slugify'] = utils.cnslugify
    jenv.filters['tohtml'] = utils.cntohtml
    return jenv

def toEdxProblemXml(question):
    """ given a question object, return EDX Xml """
    return question.toEDX()


def generateEDXArchive(module, moduleOutDir):
    """ Given a module object and destination dir, generate EDX archive """

    # Module data
    module.advanced_EDX_module_list = EDX_ADVANCED_MODULE_LIST.__str__()

    # create EDX archive temp folder
    edx_outdir = os.path.join(moduleOutDir, 'EDX')
    os.makedirs(edx_outdir)

    # generate content files: html/webcontent | problem/(Activite|ActiviteAvancee|Comprehension)
    for sec in module.sections:
        for sub in sec.subsections:
            if sub.folder == 'webcontent': # these go to EDX/html/
                utils.write_file(sub.html_src, edx_outdir, 'html', sub.getFilename() )
            elif sub.folder in ('Activite', 'ActiviteAvancee', 'Comprehension'):
                for question in sub.questions:
                    fname =  ('%s.xml' % question.id)
                    utils.write_file(toEdxProblemXml(question), edx_outdir, 'problem', fname )

    # Add other files
    for folder, dfile in EDX_DEFAULT_FILES.items():
        shutil.copytree(os.path.join(EDX_TEMPLATES_PATH, folder), os.path.join(edx_outdir,folder))

    # Render and add policies/course files
    course_policies_files =  ['grading_policy.json', 'policy.json']

    jenv = loadJinjaEnv()
    for pfile in course_policies_files:
        pfile_template = jenv.get_template(os.path.join('policies','course', pfile))
        pjson = pfile_template.render(module=module)
        pjson = json.dumps(json.loads(pjson),ensure_ascii=True,indent=4,separators=(',', ': '))
        utils.write_file(pjson, os.getcwd(), os.path.join(edx_outdir, 'policies', 'course'), pfile)


    # Write main course.xml file
    course_template = jenv.get_template("course.tmpl.xml")
    course_xml = course_template.render(module=module, grademap=EDX_GRADER_MAP)
    utils.write_file(course_xml, os.getcwd(), edx_outdir, 'course.xml')

    # pack it up into a tar archive
    archive_file = os.path.join(moduleOutDir, ('%s_edx.tar.gz' % module.module))
    with tarfile.open(archive_file, "w:gz") as tar:
        for afile in os.listdir(edx_outdir):
            tar.add(os.path.join(edx_outdir, afile))
    tar.close()

    return ('%s_edx.tar.gz' % module.module)


def generateEDXArchiveLight(module, moduleOutDir, zipFile):
    """ Given a module object and destination dir, generate EDX archive """

    # Module data
    module.advanced_EDX_module_list = EDX_ADVANCED_MODULE_LIST.__str__()

    edx_outdir = os.path.join(moduleOutDir, 'EDX')

    # generate content files: html/webcontent | problem/(Activite|ActiviteAvancee|Comprehension)
    for sec in module.sections:
        for sub in sec.subsections:
            if sub.folder == 'webcontent': # these go to EDX/html/
                html_outdir = os.path.join(edx_outdir, 'html', sub.getFilename())
                zipFile.writestr(html_outdir, sub.html_src.encode("UTF-8"))
                #zipFile.writestr(module.module+'/EDX/html/'+sub.getFilename(), sub.html_src.encode("UTF-8"))
            elif sub.folder in ('Activite', 'ActiviteAvancee', 'Comprehension'):
                for question in sub.questions:
                    fname =  ('%s.xml' % question.id)
                    problem_outdir = os.path.join(edx_outdir,'problem', fname)
                    zipFile.writestr(problem_outdir, toEdxProblemXml(question).encode("UTF-8"))
                    #zipFile.writestr(module.module+'/EDX/problem/'+fname, toEdxProblemXml(question).encode("UTF-8"))


    # Add other files
    for folder, dfile in EDX_DEFAULT_FILES.items():
        with open(EDX_TEMPLATES_PATH+'/'+folder+'/'+dfile, 'r') as myfile:
            data=myfile.read()
            file_path = os.path.join(edx_outdir,folder,dfile)
            zipFile.writestr(file_path, data.encode("UTF-8"))
            #zipFile.writestr(module.module+'/EDX/'+folder+'/'+dfile, data.encode("UTF-8"))

    # Render and add policies/course files
    course_policies_files =  ['grading_policy.json', 'policy.json']

    jenv = loadJinjaEnv()
    for pfile in course_policies_files:
        pfile_template = jenv.get_template(os.path.join('policies','course', pfile))
        pjson = pfile_template.render(module=module)
        pjson = json.dumps(json.loads(pjson),ensure_ascii=True,indent=4,separators=(',', ': '))
        json_path=os.path.join(edx_outdir,'policies/course',pfile)
        zipFile.writestr(json_path, pjson.encode("UTF-8"))
        #zipFile.writestr(module.module+'/EDX/policies/course/'+pfile, pjson.encode("UTF-8"))

    # Write main course.xml file
    course_template = jenv.get_template("course.tmpl.xml")
    course_xml = course_template.render(module=module, grademap=EDX_GRADER_MAP)
    course_path=os.path.join(edx_outdir,'course.xml')
    zipFile.writestr(course_path, course_xml.encode("UTF-8"))
    #zipFile.writestr(module.module+'/EDX/course.xml', course_xml.encode("UTF-8"))

    # pack it up into a tar archive
    # by using regex to determine which file must be included in that archive
    # (we have to look into the zip being generated)
    tab=zipFile.namelist()
    reEdxPath = re.compile('^'+module.module+'/EDX')

    tarArchiveIO = StringIO.StringIO()

    # We open the tar archive inside of the StringIO instance
    with tarfile.open(mode='w:gz', fileobj=tarArchiveIO) as tar:
        #for each EDX element belonging to the module
        for elt in tab:
            res=reEdxPath.match(elt)
            if res:
                # adding the file to the tar archive
                # (we need tarInfo and StringIO instance for not writing anything on the disk)
                data=zipFile.read(elt)
                info=tarfile.TarInfo(name=elt)
                info.size=len(data)
                tar.addfile(tarinfo=info, fileobj=StringIO.StringIO(data))
        tar.close()

    tarArchiveIO.seek(0)
    zipFile.writestr(module.module+'/'+module.module+'_edx.tar.gz', tarArchiveIO.read())

    return zipFile
