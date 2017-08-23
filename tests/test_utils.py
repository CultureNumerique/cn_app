import os
import unittest
import urllib2
import requests
import shutil
from mock import Mock
import logging
import sys
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..'))
from src import utils

# Ignore Warning
logger = logging.getLogger()
logger.setLevel(40)

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def connection_error():
    raise requests.exceptions.ConnectionError


def oserror():
    raise OSError(2, 'message')


osErrorMock = Mock(side_effect=OSError)


class UtilsTestCase(unittest.TestCase):

    def test_fetch_vimeo_thumb(self):
        video1 = 'https://vimeo.com/68856967'
        try:
            req = urllib2.Request('http://www.google.fr')
            urllib2.urlopen(req)
            self.assertTrue('http://i.vimeocdn.com/video/441364174_640.jpg' in utils.fetch_vimeo_thumb(video1))
        except Exception:
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

    def test_createEmptyFile(self):
        new_file = "./new_file"
        #CREATE FILE
        utils.create_empty_file_if_needed(new_file)
        self.assertTrue(os.path.isfile(new_file))
        #FILE ALREADY EXISTED
        utils.create_empty_file_if_needed(new_file)
        self.assertTrue(os.path.isfile(new_file))
        if os.path.isfile(new_file):
            os.remove(new_file)
        #TODO : base


    def test_fetchMarkdownFile(self):
        self.assertTrue('./coursTest/module1/module_test.md' in utils.fetchMarkdownFile('./coursTest/module1'))
        self.assertFalse(utils.fetchMarkdownFile('./'))

    def test_prepareDestination(self):
        rep1 = './testUtils'
        utils.prepareDestination('./../', rep1)
        for d in utils.STATIC_FOLDERS:
            self.assertTrue(d,('./..'+d))
        shutil.rmtree(rep1)

    def test_prepareDestinationError(self):
        rep1 = './testUtils'
        utils.STATIC_FOLDERS.append('static/css')
        # with patch('shutil.copytree', new=Mock(side_effect=OSError())):
        utils.prepareDestination('./..', rep1)
        utils.prepareDestination('./dpzoq', rep1)
        shutil.rmtree(rep1)

    def test_createDirs(self):
        rep1 = '../testUtils'
        folders = utils.STATIC_FOLDERS
        utils.createDirs(rep1, folders)
        for f in folders:
            self.assertTrue(os.path.isdir(rep1+'/'+f))
        shutil.rmtree(rep1)

    def test_copyMediaDirs(self):
        utils.copyMediaDir('./coursTest', './outdir', 'module1')
        self.assertTrue(os.path.isfile('./outdir/media/Logo_cercle_vert.svg'))
        utils.copyMediaDir('./coursTest', './outdir', 'module1')
        self.assertTrue(os.path.isfile('./outdir/media/Logo_cercle_vert.svg'))
        if (os.path.isfile('./outdir/media/Logo_cercle_vert.svg')):
            shutil.rmtree('./outdir')


# Main
if __name__ == '__main__':
    unittest.main(verbosity=1)
