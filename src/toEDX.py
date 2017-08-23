# -*- coding: utf-8 -*-

import json
import os
import shutil
import tarfile

from io import open
from jinja2 import Environment, FileSystemLoader

import utils
import re
import StringIO

from cnSettings import EDX_TEMPLATES_PATH, EDX_DEFAULT_FILES, EDX_ADVANCED_MODULE_LIST, EDX_GRADER_MAP, EDX_DIRECTORY

reMediaPath = re.compile('/\w*/media/')


def loadJinjaEnv():
    jenv = Environment(loader=FileSystemLoader(EDX_TEMPLATES_PATH))
    jenv.filters['slugify'] = utils.cnslugify
    jenv.filters['tohtml'] = utils.cntohtml
    return jenv


def generateEDXArchive(module, moduleOutDir):
    """ Given a module object and destination dir, generate EDX archive """

    # Module data
    module.advanced_EDX_module_list = EDX_ADVANCED_MODULE_LIST.__str__()

    # create EDX archive temp folder
    edx_outdir = os.path.join(moduleOutDir, EDX_DIRECTORY)
    os.makedirs(edx_outdir)

    # generate content files:
    # html/webcontent | problem/(Activite|ActiviteAvancee|Comprehension)
    for sec in module.sections:
        for sub in sec.subsections:
            if sub.folder == 'webcontent':
                # these go to EDX/html/
                utils.write_file(sub.html_src,
                                 edx_outdir,
                                 'html',
                                 sub.getFilename())
            elif sub.folder in ('Activite',
                                'ActiviteAvancee',
                                'Comprehension'):
                for question in sub.questions:
                    fname = ('%s.xml' % question.id)
                    utils.write_file(question.toEDX(),
                                     edx_outdir,
                                     'problem',
                                     fname)

    # Add other files
    for folder, dfile in EDX_DEFAULT_FILES.items():
        shutil.copytree(os.path.join(EDX_TEMPLATES_PATH, folder),
                        os.path.join(edx_outdir, folder))

    # Render and add policies/course files
    course_policies_files = ['grading_policy.json', 'policy.json']

    jenv = loadJinjaEnv()
    for pfile in course_policies_files:
        pfile_template = jenv.get_template(os.path.join('policies',
                                                        'course',
                                                        pfile))
        pjson = pfile_template.render(module=module)
        pjson = json.dumps(json.loads(pjson),
                           ensure_ascii=True,
                           indent=4,
                           separators=(',', ': '))
        utils.write_file(pjson,
                         os.getcwd(),
                         os.path.join(edx_outdir,
                                      'policies',
                                      'course'),
                         pfile)

    # Write main course.xml file
    course_template = jenv.get_template("course.tmpl.xml")
    course_xml = course_template.render(module=module, grademap=EDX_GRADER_MAP)
    utils.write_file(course_xml, os.getcwd(), edx_outdir, 'course.xml')

    # pack it up into a tar archive
    archive_file = os.path.join(moduleOutDir,
                                ('%s_edx.tar.gz' % module.name))
    with tarfile.open(archive_file, "w:gz") as tar:
        for afile in os.listdir(edx_outdir):
            tar.add(os.path.join(edx_outdir, afile),
                    os.path.join(module.name, afile))
    tar.close()


def generateEDXArchiveIO(module,
                         mediaFiles,
                         mediaNames):
    """
    Writes the EDX content in a zipfile and returns that zipfile.
    The structure of this archive is contained in a tree /<EDX_DIRECTORY>/
    (usually EDX_DIRECTORY=EDX) and returns the zipfile.
    """

    # We open the tar archive inside of the StringIO instance
    tarArchiveIO = StringIO.StringIO()
    tar = tarfile.open(mode='w:gz', fileobj=tarArchiveIO)

    # Module data
    module.advanced_EDX_module_list = EDX_ADVANCED_MODULE_LIST.__str__()
    # edx_outdir = os.path.join(moduleOutDir, EDX_DIRECTORY)
    edx_archivedir = EDX_DIRECTORY

    # generate content files:
    # html/webcontent | problem/(Activite|ActiviteAvancee|Comprehension)
    for sec in module.sections:
        for sub in sec.subsections:
            if sub.folder == 'webcontent':
                # these go to EDX/html/
                html = sub.rebaseMediaLinks('/static/').encode("UTF-8")
                html_outdir = os.path.join(edx_archivedir,
                                           'html',
                                           sub.getFilename())
                utils.writetarstr(tar, html_outdir, html)
            elif sub.folder in ('Activite',
                                'ActiviteAvancee',
                                'Comprehension'):
                for question in sub.questions:
                    fname = ('%s.xml' % question.id)
                    problem_outdir = os.path.join(edx_archivedir,
                                                  'problem',
                                                  fname)
                    xml = reMediaPath.sub('/static/',
                                          question.toEDX()).encode("UTF-8")
                    utils.writetarstr(tar,
                                      problem_outdir,
                                      xml)

    if mediaFiles:
        # add media files in '/EDX/static'
        for media, name in zip(mediaFiles, mediaNames):
            media.seek(0)
            utils.writetarstr(tar,
                              edx_archivedir+'/static/'+name,
                              media.read())

    # Add other files
    for folder, dfile in EDX_DEFAULT_FILES.items():
        with open(EDX_TEMPLATES_PATH+'/'+folder+'/'+dfile, 'r') as myfile:
            data = myfile.read()
            file_path = os.path.join(edx_archivedir,
                                     folder,
                                     dfile)
            utils.writetarstr(tar, file_path, data.encode("UTF-8"))

    # Render and add policies/course files
    course_policies_files = ['grading_policy.json', 'policy.json']

    jenv = loadJinjaEnv()
    for pfile in course_policies_files:
        pfile_template = jenv.get_template(os.path.join('policies',
                                                        'course',
                                                        pfile))
        pjson = pfile_template.render(module=module)
        pjson = json.dumps(json.loads(pjson),
                           ensure_ascii=True,
                           indent=4,
                           separators=(',', ': '))
        json_path = os.path.join(edx_archivedir,
                                 'policies/course',
                                 pfile)
        utils.writetarstr(tar, json_path, pjson.encode("UTF-8"))

    # Write main course.xml file
    course_template = jenv.get_template("course.tmpl.xml")
    course_xml = course_template.render(module=module, grademap=EDX_GRADER_MAP)
    course_path = os.path.join(edx_archivedir,
                               'course.xml')
    utils.writetarstr(tar,
                      course_path,
                      course_xml.encode("UTF-8"))

    tar.close()

    return tarArchiveIO
