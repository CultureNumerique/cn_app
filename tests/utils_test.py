import sys, os
sys.path.insert(0, os.path.abspath('..'))
import unittest
import urllib2
import requests
import shutil
import exceptions
from mock import MagicMock

from urlparse import urlparse


# Ignore Warning
import logging
logger = logging.getLogger()
logger.setLevel(40)

from src import utils

BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def connection_error():
    raise requests.exceptions.ConnectionError

class UtilsTestCase(unittest.TestCase):

    def test_fetch_vimeo_thumb(self):
        video1 = 'https://vimeo.com/68856967'
        req = urllib2.Request('http://www.google.fr')
        try:
            urllib2.urlopen(req)
            self.assertTrue('http://i.vimeocdn.com/video/441364174_640.jpg' in utils.fetch_vimeo_thumb(video1))
        except e:
            print "Connect Error:", e.reason[1]
            self.assertTrue('https://i.vimeocdn.com/video/536038298_640.jpg' in utils.fetch_vimeo_thumb(video1))
        # FIXME : Simulate an error connection to test the part Exception of fetch_vimeo_thumb
        # requests.get = MagicMock(side_effect=connection_error)
        # with requests.exceptions.ConnectionError:
        #     resp = utils.fetch_vimeo_thumb(video1)
        # self.assertTrue('https://i.vimeocdn.com/video/536038298_640.jpg' in resp)


    def test_get_embed_code_for_url(self):
        video1 = 'https://vimeo.com/123456789'
        (hst1, ec1) = utils.get_embed_code_for_url(video1)
        self.assertTrue('vimeo.com' in hst1)
        self.assertTrue('<iframe src="https://player.vimeo.com/video/123456789" width="500" '+
'height="281" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>' in ec1)
        video2 = 'https://www.canal-u.tv/123456789'
        (hst2, ec2) = utils.get_embed_code_for_url(video2)
        self.assertTrue('www.canal-u.tv' in hst2)
        self.assertTrue('<iframe src="https://www.canal-u.tv/embed.1/123456789?width=100%&amp;height=100%&amp" width="550" '+
'height="306" frameborder="0" allowfullscreen scrolling="no"></iframe>' in ec2)
        video3 = 'https://youtube.com/123456789'
        (hst3, ec3) = utils.get_embed_code_for_url(video3)
        self.assertTrue('youtube.com' in hst3)
        self.assertTrue('<p>Unsupported video provider ({0})</p>'.format(hst3) in ec3)

    def test_get_video_src(self):
        video1 = 'https://vimeo.com/68856967'
        src = utils.get_video_src(video1)
        self.assertTrue('https://player.vimeo.com/video/68856967' in src)
        video2 = 'https://youtube.com/123456789'
        src = utils.get_video_src(video2)

    def test_add_target_blanc(self):
        src = "<a Blablabla />"
        src2 = "<p> Blebleble </p>"
        self.assertTrue('_blank' in utils.add_target_blank(src))
        self.assertFalse('_blank' in utils.add_target_blank(src2))

    def test_write_file(self):
        current = os.getcwd()
        src = "My Text"
        folder = "Test_Write_File"
        name = "New_File"
        #NO EXCEPT
        rt = utils.write_file(src, current, folder, name)
        self.assertTrue('Test_Write_File/New_File' in rt)
        self.assertTrue(os.path.isdir('./'+folder))
        self.assertTrue(os.path.exists(rt))
        try:
            shutil.rmtree('./'+folder, ignore_errors=True)
        except Exception:
            pass
        #EXCEPT
        # TODO

    # def test_createDirs(self):
    #     folders = ['d1', 'd2', 'd3']
    #
    # def test_fetchMarkdownFile(self):
    #     self.assertTrue('./coursTest/module1/module_test.md' in utils.fetchMarkdownFile('./coursTest/module1'))
    #     self.assertFalse(utils.fetchMarkdownFile('./'))
    #
    # def test_prepareDestination(self):
    #
    #     utils.prepareDestination('BASE_PATH','testUtils')

# Main
if __name__ == '__main__':
    unittest.main(verbosity=1)
