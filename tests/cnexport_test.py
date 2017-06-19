import sys, os
sys.path.insert(0, os.path.abspath('..'))
from io import open
import unittest
import logging
import mock
logger = logging.getLogger()
logger.setLevel(40)

from src import cnExport

TEST_CNEXPORT_DIR = './dirmodule'

def setUp():
    try :
        os.makedirs(TEST_CNEXPORT_DIR)
    except :
        pass
#     with open("coursTest/module1/module_test.md", encoding='utf-8') as sample_file:
#         global m
#         m = model.Module(sample_file, "tests", "http://culturenumerique.univ-lille3.fr")


# class CnExportTestCase(unittest.TestCase):

    # def test_writeHtml(self):
    #     html = u"<p>Text</p>"
    #     m = 'module'
    #     cnExport.writeHtml(m, TEST_CNEXPORT_DIR, html)
    #     self.assertTrue(os.path.isdir(TEST_CNEXPORT_DIR))
    #     self.assertTrue(os.path.exists(TEST_CNEXPORT_DIR+'/'+m+'.html'))

    # def test_processModule(self):




# Main
if __name__ == '__main__':
    setUp()
    unittest.main(verbosity=1)
