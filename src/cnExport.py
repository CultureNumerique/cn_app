# -*- coding: utf-8 -*-
import argparse
import os
import sys
import logging
import glob

from io import open

import utils
import toIMS
import toEDX
import toHTML
import model
from cnSettings import BASE_PATH


def writeHtml(module, outModuleDir, html):
    """
    """
    module_file_name = os.path.join(outModuleDir, module)+'.html'
    moduleHtml = open(module_file_name, 'w', encoding='utf-8')
    moduleHtml.write(html)
    moduleHtml.close()


def processModule(args, source_dir, out_dir, module_name):
    """given input paramaters, process a module. Outputs are generated in
    directory module_name under out_dir.

        :param args: Namespace result of parser.parse_args
        :param out_dir: output directory
        :param module_name: module name

    """

    moduleDir = os.path.join(source_dir, module_name)
    moduleOutDir = os.path.join(out_dir, module_name)
    utils.copyMediaDir(source_dir, moduleOutDir, module_name)

    # Fetch and parse md file
    filein = utils.fetchMarkdownFile(moduleDir)
    with open(filein, encoding='utf-8') as md_file:
        m = model.Module(md_file, module_name, args.baseUrl)

    # check if there is a logo
    logopath = os.path.join(moduleDir, "logo.png")
    if os.path.exists(logopath):
        m.logo_filename = logopath

    # HTML output (necessary for any output)
    m.toHTML(args.feedback)  # only generate html for all subsections

    # gift files
    if not args.no_gift:
        utils.write_file(m.toGift(),
                         moduleOutDir,
                         '',
                         module_name+'.questions_bank.gift.txt')
    # Video list
    if not args.no_video:
        utils.write_file(m.toVideoList(),
                         moduleOutDir,
                         '',
                         module_name+'.video_iframe_list.txt')

    # EDX files
    if args.edx:
        m.edx_archive_path = toEDX.generateEDXArchive(m, moduleOutDir)

    # # if chosen, generate IMS archive
    if args.ims:
        m.ims_archive_path = toIMS.generateIMSArchive(m, moduleOutDir)
        logging.warn('*Path to IMS = %s*' % m.ims_archive_path)

    # return module object
    return m


def processRepository(args, repoDir, outDir):
    """ takes arguments and directories and process repository  """
    os.chdir(repoDir)
    course_program = model.CourseProgram(args.title, repoDir)
    # first checks
    if args.modules is None:
        listt = glob.glob("module[0-9]")
        args.modules = sorted(listt, key=lambda a: a.lstrip('module'))

    for module in args.modules:
        logging.info("\nStart Processing %s", module)
        course_program.modules.append(processModule(args,
                                                    repoDir,
                                                    outDir,
                                                    module))

    return course_program


# ############## main ################
if __name__ == "__main__":

    # utf8 hack, python 2 only !!
    if sys.version_info[0] == 2:
        print("reload default encoding")
        reload(sys)
        sys.setdefaultencoding('utf8')

    # ** Parse arguments **
    parser = argparse.ArgumentParser(description="Parses markdown files and generates a website using index.tmpl in the current directory. Default is to process and all folders 'module*'.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--modules", help="module folders", nargs='*')
    parser.add_argument("-l", "--log", dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING',
                                 'ERROR', 'CRITICAL'],
                        help="Set the logging level", default='WARNING')
    parser.add_argument("-L", "--logfile", dest="logfile",
                        help="log file.", default=LOGFILE)
    parser.add_argument("-r", "--repository",
                        help="Set the repository source dir containing the moduleX dirs, given as absolute or relative to cn_app dir",
                        default='repositories/culturenumerique/cn_modules')
    parser.add_argument("-d", "--destination",
                        help="Set the destination dir",
                        default='build')
    parser.add_argument("-t", "--title",
                        help="Title of the course program",
                        default='Culture numérique')
    parser.add_argument("-u", "--baseUrl",
                        help="Set the base url for absolute url building",
                        default='http://culturenumerique.univ-lille3.fr')
    parser.add_argument("-f", "--feedback",
                        action='store_true',
                        help="Add feedbacks for all questions in web export",
                        default=False)
    parser.add_argument("-i", "--ims",
                        action='store_true',
                        help="Also generate IMS archive for each module",
                        default=False)
    parser.add_argument("-H", "--no-html",
                        action='store_true',
                        help="do not generate HTML files",
                        default=False)
    parser.add_argument("-G", "--no-gift",
                        action='store_true',
                        help="do not generate GIFT bank file",
                        default=False)
    parser.add_argument("-V", "--no-video",
                        action='store_true',
                        help="do not generate video list file",
                        default=False)
    parser.add_argument("-e", "--edx",
                        action='store_true',
                        help="Also generate EDX archive for each module",
                        default=False)
    args = parser.parse_args()

    # ** Logging **
    utils.create_empty_file_if_needed(args.logfile)
    logging.basicConfig(filename=args.logfile,
                        filemode='a',
                        level=getattr(logging, args.logLevel))

    # ** Paths and directories **
    if os.path.isabs(args.repository):
        repoDir = args.repository
    else:
        repoDir = os.path.join(BASE_PATH, args.repository)
    logging.warn("repository directory path : %s" % repoDir)
    if not(os.path.exists(repoDir)):
        sys.exit("Error : repository directory provided does not exist")
    if ((args.destination == '.') or
        (args.destination.rstrip('/') == os.getcwd())):
        sys.exit("Error: cannot build within current directory.")
    if os.path.isabs(args.destination):
        outDir = args.destination
    else:
        outDir = os.path.join(repoDir, args.destination)
    utils.prepareDestination(BASE_PATH, outDir)

    # ** Process repository **
    course_program = processRepository(args, repoDir, outDir)

    # ** Build site **
    if not args.no_html:
        toHTML.buildSite(course_program, repoDir, outDir)

    # ** Exit and print path to build files: **
    os.chdir(BASE_PATH)
    print("**Build successful!** See result in : %s" % outDir)
    sys.exit(0)
