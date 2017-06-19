#!cnappenv/bin/python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import logging
import shutil
import glob

import markdown
from io import open
from jinja2 import Environment, FileSystemLoader

import utils
import toIMS
import toEDX
import model


MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TEMPLATES_PATH = os.path.join(BASE_PATH, 'templates' )
LOGFILE = 'logs/cnExport.log'

def writeHtml(module, outModuleDir, html):
    """
    """
    module_file_name = os.path.join(outModuleDir, module)+'.html'
    moduleHtml = open(module_file_name, 'w', encoding='utf-8')
    moduleHtml.write(html)
    moduleHtml.close()


def processModule(args, repoDir, outDir, module):
    """ given input paramaters, process a module  """

    moduleDir = os.path.join(repoDir, module)
    moduleOutDir = os.path.join(outDir,module)
    utils.copyMediaDir(repoDir, moduleOutDir, module)

    # Fetch and parse md file
    filein = utils.fetchMarkdownFile(moduleDir)
    with open(filein, encoding='utf-8') as md_file:
        m = model.Module(md_file, module, args.baseUrl)

    m.toHTML(args.feedback) # only generate html for all subsections

    # write html, XML, and JSon files
    utils.write_file(m.toGift(), moduleOutDir, '', module+'.questions_bank.gift.txt')
    utils.write_file(m.toVideoList(), moduleOutDir, '', module+'.video_iframe_list.txt')

    # EDX files
    if args.edx:
        m.edx_archive_path = toEDX.generateEDXArchive(m, moduleOutDir)

    # # if chosen, generate IMS archive
    if args.ims:
        m.ims_archive_path = toIMS.generateImsArchive(m, module, moduleOutDir)
        logging.warn('*Path to IMS = %s*' % m.ims_archive_path)

    # return module object
    return m

def processRepository(args, repoDir, outDir):
    """ takes arguments and directories and process repository  """
    os.chdir(repoDir)
    course_obj = model.CourseProgram(repoDir)
    # first checks
    if args.modules == None:
        listt = glob.glob("module[0-9]")
        args.modules = sorted(listt,key=lambda a: a.lstrip('module'))

    for module in args.modules:
        logging.info("\nStart Processing %s", module)
        course_obj.modules.append(processModule(args, repoDir, outDir, module))

    return course_obj


def buildSite(course_obj, repoDir, outDir):
    """ Generate full site from result of parsing repository """

    jenv = Environment(loader=FileSystemLoader(TEMPLATES_PATH))
    jenv.filters['slugify'] = utils.cnslugify
    site_template = jenv.get_template("site_layout.html")
    #if found, copy logo.png, else use default
    logo_files = glob.glob(os.path.join(repoDir, 'logo.*'))
    if len(logo_files) > 0:
        logo = logo_files[0].rsplit('/',1)[1]
        try:
            shutil.copy(logo, outDir)
        except Exception as e:
            logging.warn(" Error while copying logo file %s" % e)
            pass
    else:# use default one set in template
        logo = 'default'

    ## open and parse 1st line title.md
    try:
        title_file = os.path.join(repoDir, 'title.md')
        with open(title_file, 'r', encoding='utf-8') as f:
            course_obj.title = f.read().strip()
    except Exception as e:
        logging.warn(" Error while parsing title file %s" % e)
        pass

    # Create site index.html with home.md content
    ## open and parse home.md
    custom_home = False
    try:
        home_file = os.path.join(repoDir, 'home.md')
        with open(home_file, 'r', encoding='utf-8') as f:
            home_data = f.read()
        home_html = markdown.markdown(home_data, MARKDOWN_EXT)
        custom_home = True
    except Exception:
        ## use default from template
        logging.error(" Cannot parse home markdown ")
        with open(os.path.join(TEMPLATES_PATH, 'default_home.html'), 'r', encoding='utf-8') as f:
            home_html = f.read()
    ## write index.html file
    html = site_template.render(course=course_obj, module_content=home_html,body_class="home", logo=logo, custom_home=custom_home)
    utils.write_file(html, os.getcwd(), outDir, 'index.html')

    # Loop through modules
    for module in course_obj.modules:
        module_template = jenv.get_template("module.html")
        module_html_content = module_template.render(module=module)
        html = site_template.render(course=course_obj, module_content=module_html_content, body_class="modules", logo=logo)
        utils.write_file(html, os.getcwd(), outDir, module.module+'.html')


############### main ################
if __name__ == "__main__":

    # utf8 hack, python 2 only !!
    if sys.version_info[0] == 2:
        print ("reload default encoding")
        reload(sys)
        sys.setdefaultencoding('utf8')

    # ** Parse arguments **
    parser = argparse.ArgumentParser(description="Parses markdown files and generates a website using index.tmpl in the current directory. Default is to process and all folders 'module*'.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--modules",help="module folders",nargs='*')
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Set the logging level", default='WARNING')
    parser.add_argument("-r", "--repository", help="Set the repositorie source dir containing the moduleX dirs, given as absolute or relative to cn_app dir", default='repositories/culturenumerique/cn_modules')
    parser.add_argument("-d", "--destination", help="Set the destination dir", default='build')
    parser.add_argument("-u", "--baseUrl", help="Set the base url for absolute url building", default='http://culturenumerique.univ-lille3.fr')
    parser.add_argument("-f", "--feedback", action='store_true', help="Add feedbacks for all questions in web export", default=False)
    parser.add_argument("-i", "--ims", action='store_true', help="Also generate IMS archive for each module", default=False)
    parser.add_argument("-e", "--edx", action='store_true', help="Also generate EDX archive for each module", default=False)
    args = parser.parse_args()

    # ** Logging **
    logfile = utils.create_empty_file(os.path.join(BASE_PATH, 'logs'), 'cnExport.log')
    logging.basicConfig(filename=logfile,filemode='w',level=getattr(logging, args.logLevel))
    # FIXME : PACKAGE LOGGING POUR LA GESTION D'ERREUR !

    # ** Paths and directories **
    if os.path.isabs(args.repository):
        repoDir = args.repository
    else:
        repoDir = os.path.join(BASE_PATH, args.repository)
    logging.warn("repository directory path : %s" % repoDir)
    if not(os.path.exists(repoDir)):
        sys.exit("Error : repository directory provided does not exist")
    if (args.destination == '.') or (args.destination.rstrip('/') == os.getcwd()):
        sys.exit("Error: cannot build within current directory.")
    if os.path.isabs(args.destination):
        outDir = args.destination
    else:
        outDir = os.path.join(repoDir, args.destination)
    utils.prepareDestination(BASE_PATH, outDir)

    # ** Process repository **
    course_obj = processRepository(args, repoDir, outDir)

    # ** Build site **
    buildSite(course_obj, repoDir, outDir)

    # ** Exit and print path to build files: **
    os.chdir(BASE_PATH)
    print("**Build successful!** See result in : %s" % outDir)
    sys.exit(0)
