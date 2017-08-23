#!/usr/bin/env python3

"""
This file launches all the tests.

Source used :
    http://agiletesting.blogspot.com/2005/01/python-unit-testing-part-1-unittest.html
"""

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system('python test_model.py')
os.system('python test_edx.py')
os.system('python test_ims.py')
os.system('python test_utils.py')
os.system('python test_cnexport.py')
