#!/usr/bin/env python3

"""
This file launches all the tests.

Source used :
    http://agiletesting.blogspot.com/2005/01/python-unit-testing-part-1-unittest.html
"""

import sys, os
sys.path.insert(0, os.path.abspath('..'))
import src
from tests import *
from pygiftparser import parser as pygift
from threading import Thread

os.system('python model_test.py')
os.system('python edx_test.py')
os.system('python ims_test.py')
os.system('python utils_test.py')
os.system('python cnexport_test.py')
