# -*- coding: utf-8 -*-
from jinja2 import Environment, FileSystemLoader
import shutil
import markdown
import utils
import glob
import os
import logging

from cnSettings import HTML_TEMPLATES_PATH, MARKDOWN_EXT


def buildSite(course_program, repoDir, outDir):
    """ Generate full site from result of parsing repository """

    jenv = Environment(loader=FileSystemLoader(HTML_TEMPLATES_PATH))
    jenv.filters['slugify'] = utils.cnslugify
    site_template = jenv.get_template("site_layout.html")
    # if found, copy logo.png, else use default
    logo_files = glob.glob(os.path.join(repoDir, 'logo.*'))
    if len(logo_files) > 0:
        logo = logo_files[0].rsplit('/', 1)[1]
        try:
            shutil.copy(logo, outDir)
        except Exception as e:
            logging.warn(" Error while copying logo file %s" % e)
            pass
    else:  # use default one set in template
        logo = 'default'

    # open and parse 1st line title.md
    try:
        title_file = os.path.join(repoDir, 'title.md')
        with open(title_file, 'r', encoding='utf-8') as f:
            course_program.title = f.read().strip()
    except Exception as e:
        logging.warn(" Error while parsing title file %s" % e)
        pass

    # Create site index.html with home.md content
    # open and parse home.md
    custom_home = False
    try:
        home_file = os.path.join(repoDir, 'home.md')
        with open(home_file, 'r', encoding='utf-8') as f:
            home_data = f.read()
        home_html = markdown.markdown(home_data, MARKDOWN_EXT)
        custom_home = True
    except Exception:
        # use default from template
        logging.error(" Cannot parse home markdown ")
        with open(os.path.join(HTML_TEMPLATES_PATH, 'default_home.html'),
                  'r', encoding='utf-8') as f:
            home_html = f.read()
    # write index.html file
    html = site_template.render(course=course_program,
                                module_content=home_html,
                                body_class="home",
                                logo=logo,
                                custom_home=custom_home)
    utils.write_file(html, os.getcwd(), outDir, 'index.html')

    # Loop through modules
    for module in course_program.modules:
        module_template = jenv.get_template("module.html")
        module_html_content = module_template.render(module=module)
        html = site_template.render(course=course_program,
                                    module_content=module_html_content,
                                    body_class="modules", logo=logo)
        utils.write_file(html, os.getcwd(), outDir, module.name+'.html')
