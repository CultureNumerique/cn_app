import os
from io import open
import unittest
import argparse
import shutil
import logging
import sys
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..'))
from src import cnExport, model
os.chdir(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger()
logger.setLevel(40)


TEST_CNEXPORT_DIR = './out'


class CnExportTestCase(unittest.TestCase):

    def setUp(self):
        try:
            shutil.rmtree(TEST_CNEXPORT_DIR)
        except:
            pass
        try:
            os.makedirs(TEST_CNEXPORT_DIR)
        except:
            pass

    def tearDown(self):
        try:
            shutil.rmtree(TEST_CNEXPORT_DIR)
        except:
            pass

    def test_writeHtml(self):
        html = u"<p>Text</p>"
        m = 'module'
        cnExport.writeHtml(m, TEST_CNEXPORT_DIR, html)
        self.assertTrue(os.path.isdir(TEST_CNEXPORT_DIR))
        self.assertTrue(os.path.exists(TEST_CNEXPORT_DIR+'/'+m+'.html'))
        html_file = open(TEST_CNEXPORT_DIR+'/'+m+'.html')
        lines = html_file.readlines()
        self.assertTrue(html in lines[0])

    def test_processModule(self):
        # SET UP
        args = argparse.Namespace()
        args.baseUrl = 'http://example.com'
        args.feedback = False
        args.no_gift = False
        args.no_video = False
        args.edx = True
        args.ims = True
        with open("coursTest/module1/module_test.md",
                  encoding='utf-8') as sample_file:
            m1 = model.Module(sample_file,
                              "module1",
                              "http://example.com")
            m2 = cnExport.processModule(args,
                                        './coursTest',
                                        TEST_CNEXPORT_DIR,
                                        'module1')
            self.assertTrue(
                os.path.isdir(os.path.join(TEST_CNEXPORT_DIR,
                                           'module1')))
            self.assertTrue(
                os.path.isdir(os.path.join(TEST_CNEXPORT_DIR,
                                           'module1',
                                           'media')))
            self.assertTrue(os.path.exists(
                os.path.join(TEST_CNEXPORT_DIR,
                             'module1',
                             'module1.questions_bank.gift.txt')))
            self.assertTrue(os.path.exists(
                os.path.join(TEST_CNEXPORT_DIR,
                             'module1',
                             'module1.video_iframe_list.txt')))
            self.assertTrue(m1.name == m2.name)


# Main
if __name__ == '__main__':
    unittest.main(verbosity=1)
