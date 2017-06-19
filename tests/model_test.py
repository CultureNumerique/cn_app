 #!/usr/bin/ python
# -*- coding: utf-8 -*-

from io import open
import json
import mock
import unittest
from collections import namedtuple
from StringIO import StringIO
from jinja2 import Template, Environment, FileSystemLoader
# Path hack for getting access to src python modules
import sys, os
sys.path.insert(0, os.path.abspath('..'))

# Ignore Warning
import logging
logger = logging.getLogger()
logger.setLevel(40)

from src import model,utils

"""
    Test File for Project Esc@pad : Model.py
    ==============================

    Here is a test file to test the project Esc@pad : model.py.
    This file test :
        - The parsing of a markdown course into a python object (Header,sections,subsections,activities,etc..)

    How to use this file ?
    ---------------------
    In your terminal, use the command :
        >> $ python model_tests.py


"""

class FctParserTestCase(unittest.TestCase):

    # def JSON_string_header(author, base_url, css, language, menutitle, module, title):
    #     return ("{'author': '"+author+"', 'base_url': '"+base_url+"', 'css':'"+css+"', 'language': '"+language+"','menutitle': '"+menutitle+"','module': '"+module+"','title': '"+title+"' }")

    def test_default_parser_head(self):
        """
        This method check default values of header.
        """
        # JSON control
        object_header = StringIO("""
        {
        "author": "culture numerique",
        "base_url": "http://culnu.fr",
        "css": "http://culturenumerique.univ-lille3.fr/css/base.css",
        "language": "fr",
        "menutitle": "Titre",
        "module": "culnu",
        "title": "Titre long"
        }
        """)
        control_header = json.load(object_header, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del object_header

        # Parsed MD without header
        pars_head = StringIO("""
        # Titre 1
        """)
        sample_object = model.Module(pars_head, "culnu", "http://culnu.fr")
        sample_header = json.loads(sample_object.toJson(), object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        #Test the default value of metadata
        self.assertEqual(control_header.title, sample_header.title, "Not the same title in default_parser_head")
        self.assertEqual(control_header.author, sample_header.author, "Not the same author in default_parser_head")
        self.assertEqual(control_header.base_url, sample_header.base_url, "Not the same base_url in default_parser_head")
        self.assertEqual(control_header.css, sample_header.css, "Not the same css in default_parser_head")
        self.assertEqual(control_header.language, sample_header.language, "Not the same language in default_parser_head")
        self.assertEqual(control_header.menutitle, sample_header.menutitle, "Not the same menutitle in default_parser_head")
        self.assertEqual(control_header.module, sample_header.module, "Not the same module in default_parser_head")
        print("[FctParserTestCase]-- default_parser_head OK --")

    def test_wrong_case_header(self):
        """
        Check if an incorrect data can be write
        """
        # Parsed MD without header
        pars_head = StringIO("""
TITLE: Bonjour
MENUTITLE: Salut
CHICKEN: Cot Cot
# Titre 1
        """)
        sample_object = model.Module(pars_head, "culnu", "http://culnu.fr")
        sample_header = json.loads(sample_object.toJson(), object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object


        self.assertIsNotNone(sample_header.chicken)
        print("[FctParserTestCase]-- wrong_case_header OK --")

    def test_sections(self):
        """
        """
        #Title parsed
        io_title = StringIO("""
Bla bla bla
# Title 0
### SubSub0
## Sub 0
# Title 1
Blablabla
# Title 2
# Title 3
## Sub3
### SubSub3
## Sub3.2
# Title 4
Fin
        """)
        sample_object = model.Module(io_title, "culnu", "http://culnu.fr")
        sample_sections = json.loads(sample_object.toJson(), object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        self.assertEqual(len(sample_sections.sections),5, "Not the same number of sections in check_sections")

        for i,sec in enumerate(sample_sections.sections):
            self.assertEqual(sec.title,"Title "+str(i))


        print("[FctParserTestCase]-- check_sections OK --")

    def test_subsections(self):
        """
        """
        # PARSE
        io_sub = StringIO("""
# Title 0
## Sub 00
## Sub 01
Blablabla
## Sub 02
### SubSub 03 0
## Sub 03
# Title 1
# Title 2
## Sub 20
        """)
        sample_object = model.Module(io_sub, "culnu", "http://culnu.fr")
        sample_subsections = json.loads(sample_object.toJson(), object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object


        # ASSERT NUMBERS
        self.assertEqual(len(sample_subsections.sections[0].subsections), 4, "Not the same number of subsections in check_subsections")
        self.assertEqual(len(sample_subsections.sections[1].subsections), 0, "Not the same number of subsections in check_subsections")
        self.assertEqual(len(sample_subsections.sections[2].subsections), 1, "Not the same number of subsections in check_subsections")


        #ASSERTSame
        for i,sec in enumerate(sample_subsections.sections):
            for j,sub in enumerate(sec.subsections):
                self.assertEqual(sub.title, "Sub "+str(i)+str(j))

        print("[FctParserTestCase]-- check_subsections OK --")

    def test_subsubsections(self):
        """
        """
        # PARSE
        io_subsub = StringIO("""
# Title 0
## Sub 00
### SubSub 000
Blablabla
### SubSub 001
## Sub 01
### SubSub 010
# Title 1
Blabla
### SubSub 100
        """)

        sample_object = model.Module(io_subsub, "culnu", "http://culnu.fr")
        sample_subsubsections = json.loads(sample_object.toJson(), object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        self.assertNotEquals( sample_subsubsections.sections[0].subsections[0].src.find("### SubSub 000"), -1)
        self.assertNotEquals( sample_subsubsections.sections[0].subsections[0].src.find("### SubSub 001"), -1)
        self.assertNotEquals( sample_subsubsections.sections[0].subsections[1].src.find("### SubSub 010"), -1)
        self.assertNotEquals( sample_subsubsections.sections[1].subsections[0].src.find("### SubSub 100"), -1)

        print("[FctParserTestCase]-- check_subsubsections OK --")

    def test_cours(self):
        """
        Test for parsing Cours format
        """
        io_cours = StringIO(u"""
# Title 0
Ce texte va être placé tout seul dans un cours
## Cours 0
Ce texte va être placé dans cours 0
### SubSub 000
Ce texte va être placé dans cours 0
## Cours 1
Ce texte va être placé dans cours 1
```comprehension
::Comp1::
 Hello
{
salut}
```
# Title 1

```activite
::Act1::
Je ne suis toujours pas un cours !
```

## Cours 3
Par contre moi oui !

```
        """)

        sample_object = model.Module(io_cours, "culnu", "http://culnu.fr")
        sample_cours = json.loads(sample_object.toJson(), object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object


        self.assertEqual(sample_cours.sections[0].subsections[0].title, "Cours")
        self.assertEqual(sample_cours.sections[0].subsections[0].folder, "webcontent")
        self.assertEqual(sample_cours.sections[0].subsections[0].src, 'Ce texte va être placé tout seul dans un cours\n')
        self.assertEqual(sample_cours.sections[0].subsections[1].title, "Cours 0")
        self.assertEqual(sample_cours.sections[0].subsections[1].folder, "webcontent")
        self.assertEqual(sample_cours.sections[0].subsections[1].src, 'Ce texte va être placé dans cours 0\n### SubSub 000\nCe texte va être placé dans cours 0\n')
        self.assertEqual(sample_cours.sections[0].subsections[2].title, "Cours 1")
        self.assertEqual(sample_cours.sections[0].subsections[2].folder, "webcontent")
        self.assertNotEqual(sample_cours.sections[0].subsections[3].title, "Cours")
        self.assertNotEqual(sample_cours.sections[0].subsections[3].folder, "webcontent")
        self.assertNotEqual(sample_cours.sections[1].subsections[0].title, "Cours")
        self.assertNotEqual(sample_cours.sections[1].subsections[0].folder, "webcontent")
        self.assertEqual(sample_cours.sections[1].subsections[1].title, "Cours 3")

        print("[FctParserTestCase]-- check_cours OK --")

    def testParseVideoLinks(self):
        """
        """
        io_video = """# Title 0
[MaVideo](https://vimeo.com/0123456789){: .cours_video }
        """

        class TestParseVideo(model.Cours):
            def __init__(self):
                self.src = io_video
                self.videos = []

        testvideo = TestParseVideo()
        self.assertTrue(testvideo.parseVideoLinks())

        self.assertEqual(len(testvideo.videos),1,"problem for created new video object")
        self.assertEqual(testvideo.videos[0].get("video_title"),"MaVideo")
        self.assertEqual(testvideo.videos[0].get("video_link"),"https://vimeo.com/0123456789")
        self.assertEqual(testvideo.videos[0].get("video_thumbnail"),'https://i.vimeocdn.com/video/536038298_640.jpg')

        print("[FctParserTestCase]-- check_video_parse_links OK --")


    def testvideoIframeList(self):
        """
        """
        newVideoObject = {
            'video_title':"title",
            'video_link':"link",
            'video_src_link':"src_link",
            'video_thumbnail':"thumbnail"
        }

        class TestVideoIframe(model.Cours):
            def __init__(self):
                self.num = '1'
                self.title = "hello"
                self.videos = [newVideoObject]

        testvideo = TestVideoIframe()
        testvideo.videoIframeList()



    def testSubsections(self):
        """
        Test for SubSections methods
        """
        model.Subsection.num = 1
        sc = mock.MagicMock(num='2')
        sub = model.Subsection(sc)
        sub.title = "Title"
        sub.folder = "Folder"
        self.assertEqual(sub.section, sc)
        self.assertEqual(sub.num,"2-1")
        self.assertEqual(sub.getFilename(),"2-1title_Folder.html")
        self.assertEqual(sub.getFilename(term="xml"),"2-1title_Folder.xml")

        print("[FctParserTestCase]-- class Subsection check OK --")



    def testActivites(self):
        """
        Test For reStartActivityMatch, goodActivity
        """
        io_activite = StringIO(u"""```activite
Je suis une activité
```
""")
        io_compr = StringIO(u"""```comprehension
Je suis une comprehension
```
""")
        io_actav = StringIO(u"""```activite-avancee
Je suis une Activité Avancée {
= Oui
}
```
""")
        io_rdt = StringIO(u"""```riendutout
Je suis Rien du tout
```
        """)

        io_anyact = StringIO(u"""
Je suis une AnyActivity {
= Oui
}
""")
        section = mock.MagicMock(num='1') # create Mock Object with as attribute section.num = 1

        # ANYACTIVTY
        inAct = model.AnyActivity(section,io_anyact)
        self.assertEqual(inAct.src.replace('\n',''), "Je suis une AnyActivity {= Oui}")
        self.assertEqual(inAct.lastLine,"")
        self.assertEqual(len(inAct.questions),1)

        #ACTIVITE
        matchA = model.reStartActivity.match(io_activite.readline())
        act = model.goodActivity(matchA)
        self.assertIsNotNone(act)
        self.assertEqual(act, model.Activite)
        self.assertIsNotNone(act(section,io_activite))

        #COMPREHENSION
        matchC = model.reStartActivity.match(io_compr.readline())
        comp = model.goodActivity(matchC)
        self.assertIsNotNone(comp)
        self.assertEqual(comp, model.Comprehension)
        self.assertIsNotNone(comp(section,io_compr))

        #ACTIVITEAVANCEE
        matchAA = model.reStartActivity.match(io_actav.readline())
        actav = model.goodActivity(matchAA)
        self.assertIsNotNone(model.goodActivity(matchAA))
        self.assertEqual(model.goodActivity(matchAA), model.ActiviteAvancee)
        self.assertIsNotNone(actav(section,io_actav))

        #NOTHING
        matchN = model.reStartActivity.match(io_rdt.readline())
        self.assertIsNone(model.goodActivity(matchN))

        print("[FctParserTestCase]-- anyactivity check --")


# Main
if __name__ == '__main__':
    unittest.main(verbosity=1)
