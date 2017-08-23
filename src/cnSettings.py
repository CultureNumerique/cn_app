# -*- coding: utf-8 -*-
import os

MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']
# BASE_PATH for source and dest and for templates
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HTML_TEMPLATES_PATH = os.path.join(BASE_PATH, 'templates', 'toHTML')
LOGFILE = os.path.join(BASE_PATH, 'logs', 'cnExport.log')

VIDEO_THUMB_API_URL = 'https://vimeo.com/api/v2/video/'
DEFAULT_VIDEO_THUMB_URL = 'https://i.vimeocdn.com/video/536038298_640.jpg'
DEFAULT_BASE_URL = 'http://culturenumerique.univ-lille3.fr'

EDX_TEMPLATES_PATH = os.path.join(BASE_PATH,
                                  'templates',
                                  'toEDX')
EDX_DEFAULT_FILES = {
    'about': 'overview.html',
    'assets': 'assets.xml',
    'info': 'updates.html',
    'policies': 'assets.json'
}
EDX_ADVANCED_MODULE_LIST = ['cnvideo', 'library_content']
EDX_GRADER_MAP = {
    'Activite': 'Activite',
    'ActiviteAvancee': 'Activite Avancee',
    'Comprehension': 'Comprehension',
    'webcontent': None
}

# EDX directory name (usually located in each modules directory)
EDX_DIRECTORY = 'EDX'

# IMS directory name (usually located in each modules directory)
IMS_DIRECTORY = 'IMS'

# folders associated with activity types
FOLDERS = ['Activite', 'ActiviteAvancee', 'Comprehension', 'webcontent']
