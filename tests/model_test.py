 #!/usr/bin/ python
# -*- coding: utf-8 -*-

import json
import mock
import unittest
from collections import namedtuple
from StringIO import StringIO
from jinja2 import Environment, FileSystemLoader
import sys
import os
import logging

# Path hack for getting access to src python modules
sys.path.insert(0, os.path.abspath('..'))
from src import model, utils, fromGift, toEDX

# Ignore Warning
logger = logging.getLogger()
logger.setLevel(40)


# BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
# TEMPLATES_PATH = os.path.join(BASE_PATH, 'templates')

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
        control_header = json.load(object_header,
                                   object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del object_header

        # Parsed MD without header
        pars_head = StringIO("""
        # Titre 1
        """)
        sample_object = model.Module(pars_head, "culnu", "http://culnu.fr")
        sample_header = json.loads(sample_object.toJson(),
                                   object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        # Test the default value of metadata
        self.assertEqual(control_header.title,
                         sample_header.title,
                         "Not the same title in default_parser_head")
        self.assertEqual(control_header.author,
                         sample_header.author,
                         "Not the same author in default_parser_head")
        self.assertEqual(control_header.base_url,
                         sample_header.base_url,
                         "Not the same base_url in default_parser_head")
        self.assertEqual(control_header.css,
                         sample_header.css,
                         "Not the same css in default_parser_head")
        self.assertEqual(control_header.language,
                         sample_header.language,
                         "Not the same language in default_parser_head")
        self.assertEqual(control_header.menutitle,
                         sample_header.menutitle,
                         "Not the same menutitle in default_parser_head")
        self.assertEqual(control_header.module,
                         sample_header.module,
                         "Not the same module in default_parser_head")
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
        sample_header = json.loads(sample_object.toJson(),
                                   object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        self.assertIsNotNone(sample_header.chicken)
        print("[FctParserTestCase]-- wrong_case_header OK --")

    def test_sections(self):
        """
        test parsing of sections
        """
        # Title parsed
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
        sample_sections = json.loads(sample_object.toJson(),
                                     object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        self.assertEqual(len(sample_sections.sections),
                         5,
                         "Not the same number of sections in check_sections")

        for i, sec in enumerate(sample_sections.sections):
            self.assertEqual(sec.title, "Title " + str(i))

        print("[FctParserTestCase]-- check_sections OK --")

    def test_subsections(self):
        """
        test parsing of subsections
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
        sample_subsections = json.loads(sample_object.toJson(),
                                        object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        # ASSERT NUMBERS
        self.assertEqual(len(sample_subsections.sections[0].subsections),
                         4,
                         "Not the same number of subsections in check_subsections")
        self.assertEqual(len(sample_subsections.sections[1].subsections),
                         0,
                         "Not the same number of subsections in check_subsections")
        self.assertEqual(len(sample_subsections.sections[2].subsections),
                         1,
                         "Not the same number of subsections in check_subsections")


        # ASSERTSame
        for i, sec in enumerate(sample_subsections.sections):
            for j, sub in enumerate(sec.subsections):
                self.assertEqual(sub.title, "Sub "+str(i)+str(j))

        print("[FctParserTestCase]-- check_subsections OK --")

    def test_subsubsections(self):
        """
        test parsing of sub-subsections
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
        sample_cours = json.loads(sample_object.toJson(),
                                  object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        del sample_object

        self.assertEqual(sample_cours.sections[0].subsections[0].title,
                         "Cours")
        self.assertEqual(sample_cours.sections[0].subsections[0].folder,
                         "webcontent")
        self.assertEqual(sample_cours.sections[0].subsections[0].src,
                         'Ce texte va être placé tout seul dans un cours\n')
        self.assertEqual(sample_cours.sections[0].subsections[1].title,
                         "Cours 0")
        self.assertEqual(sample_cours.sections[0].subsections[1].folder,
                         "webcontent")
        self.assertEqual(sample_cours.sections[0].subsections[1].src,
                         'Ce texte va être placé dans cours 0\n### SubSub 000\nCe texte va être placé dans cours 0\n')
        self.assertEqual(sample_cours.sections[0].subsections[2].title,
                         "Cours 1")
        self.assertEqual(sample_cours.sections[0].subsections[2].folder,
                         "webcontent")
        self.assertNotEqual(sample_cours.sections[0].subsections[3].title,
                            "Cours")
        self.assertNotEqual(sample_cours.sections[0].subsections[3].folder,
                            "webcontent")
        self.assertNotEqual(sample_cours.sections[1].subsections[0].title,
                            "Cours")
        self.assertNotEqual(sample_cours.sections[1].subsections[0].folder,
                            "webcontent")
        self.assertEqual(sample_cours.sections[1].subsections[1].title,
                         "Cours 3")

        print("[FctParserTestCase]-- check_cours OK --")

    def testParseVideoLinks(self):
        """
        test the parsing of video links
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

        self.assertEqual(len(testvideo.videos), 1,
                         "problem for created new video object")
        self.assertEqual(testvideo.videos[0].get("video_title"),
                         "MaVideo")
        self.assertEqual(testvideo.videos[0].get("video_link"),
                         "https://vimeo.com/0123456789")
        self.assertEqual(testvideo.videos[0].get("video_thumbnail"),
                         'https://i.vimeocdn.com/video/536038298_640.jpg')

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
        listevideo = testvideo.videoIframeList()

        self.assertTrue('<iframe src=src_link width="500" height="281" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>' in listevideo)

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
        self.assertEqual(sub.num, "2-1")
        self.assertEqual(sub.getFilename(), "2-1title_Folder.html")
        self.assertEqual(sub.getFilename(term="xml"), "2-1title_Folder.xml")

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
        # create Mock Object with as attribute section.num = 1
        section = mock.MagicMock(num='1')

        # ANYACTIVTY
        inAct = model.AnyActivity(section, io_anyact)
        self.assertEqual(inAct.src.replace('\n', ''),
                         "Je suis une AnyActivity {= Oui}")
        self.assertEqual(inAct.lastLine, "")
        self.assertEqual(len(inAct.questions), 1)

        # ACTIVITE
        matchA = model.reStartActivity.match(io_activite.readline())
        act = model.goodActivity(matchA)
        self.assertIsNotNone(act)
        self.assertEqual(act, model.Activite)
        self.assertIsNotNone(act(section, io_activite))

        # COMPREHENSION
        matchC = model.reStartActivity.match(io_compr.readline())
        comp = model.goodActivity(matchC)
        self.assertIsNotNone(comp)
        self.assertEqual(comp, model.Comprehension)
        self.assertIsNotNone(comp(section, io_compr))

        # ACTIVITEAVANCEE
        matchAA = model.reStartActivity.match(io_actav.readline())
        actav = model.goodActivity(matchAA)
        self.assertIsNotNone(model.goodActivity(matchAA))
        self.assertEqual(model.goodActivity(matchAA), model.ActiviteAvancee)
        self.assertIsNotNone(actav(section, io_actav))

        # NOTHING
        matchN = model.reStartActivity.match(io_rdt.readline())
        self.assertIsNone(model.goodActivity(matchN))

        print("[FctParserTestCase]-- anyactivity check --")

    def testCourseProgram(self):

        cp = model.CourseProgram('repository')
        self.assertEqual('repository', cp.repository)
        self.assertEqual([], cp.modules)
        self.assertEqual('Culture Numérique', cp.title)
        self.assertEqual('logo.png', cp.logo_path)

    def testtoVideoList(self):
            """
            test the parsing of video links
            """

            io_video = StringIO("""# Title 0\n
## Cours\n
Blabla
[MaVideo](https://vimeo.com/0123456789){: .cours_video }\n
[Video2](https://vimeo.com/9876543210){: .cours_video }
            """)
            mod = model.Module(io_video, 'test')
            self.assertEqual(mod.sections[0].subsections[0].videoIframeList()+'\n\n',
                             mod.toVideoList())

    def testtoGift(self):
        """

        """

        io_gift = StringIO(u"""# Title 0
```comprehension
::q1::
question1
{#### GeneralFeedback}

::q2::
question2{
= Yes
~ No
~ NO
}

::q3::
ok
```
""")
        mod = model.Module(io_gift, 'test')
        gift_src = "$CATEGORY: $course$/Quiz Bank '1-1 Compréhension'"
        for q in mod.sections[0].subsections[0].questions:
            gift_src += q.source
        self.assertEqual(gift_src.replace('\n', '').strip(),
                         mod.toGift().replace('\n', '').strip())

    def testtoEdxProblemList(self):
        io_test = StringIO(u"""# Title 0
```comprehension
::q1::
question1
{#### GeneralFeedback}

::q2::
question2{
= Yes
~ No
~ NO
}

::q3::
ok
```
""")
        mod = model.Module(io_test, 'test')
        edx_list = ''
        for q in mod.sections[0].subsections[0].questions:
            edx_list += toEDX.toEdxProblemXml(q)
        self.assertEqual(edx_list.replace('\n', '').strip(),
                         mod.sections[0].subsections[0].toEdxProblemsList().replace('\n', '').strip())

    def testMediaLinks(self):
        io_media = StringIO("""# Titre 1
## Titre 2
### Titre 3
Bienvenue sur le cours [!image](media/monimage.png)
## Titre 2
blabla
        """)
        m = model.Module(io_media, 'module1')
        subsec = m.sections[0].subsections[0]
        self.assertTrue('(http://culturenumerique.univ-lille3.fr/module1/media/monimage.png)' in subsec.src)

    def testParseMedia(self):
        io_media = StringIO("""# Titre 1
## Titre 2
### Titre 3
Bienvenue sur le cours [!image](media/monimage3.png)
## Titre 2
blabla [!image](media/monimage2.png)
bloublou [!image](media/monimage3.png)
        """)
        m = model.Module(io_media, 'module1')
        subsec = m.sections[0].subsections[1]
        self.assertTrue(subsec.parseMediaLinks())
        self.assertEqual(subsec.medias[0],
                         {'media_id': 'img1-20',
                          'media_name': 'monimage2.png'})
        self.assertEqual(subsec.medias[1],
                         {'media_id': 'img1-21',
                          'media_name': 'monimage3.png'})

    def testModuleToHtml(self):
        """
        test module html
        """
        io_html = StringIO(u"""# Titre 1
## Titre 2
### Titre 3
Bienvenue sur le cours
```Comprehension
```
```Activite
```
```ActiviteAvancee
```
## Titre 22
Fin
""")
        jenv = Environment(loader=FileSystemLoader("."))
        jenv.filters['slugify'] = utils.cnslugify
        module = model.Module(io_html, 'module')
        module_template = jenv.get_template("module.html")
        module_html_content = module_template.render(module=module)
        resultat = ("""<!-- Menu gauche -->
<div class="menugauche navmenu navmenu-default navmenu-fixed-left offcanvas-sm" role="navigation" id="menugauche">
    <h1 class="icon-web">Titre</h1>

    <ul class="nav panel-group" id="accordion">

        <!-- Copier ici un item déployable -->
        <li class="panel panel-default">
            <h4 class="panel-title">
                <a href="#sec_1">
                    <span class="sec-num">1</span>
                    <span class="sec-title">Titre 1</span>
                </a>
            </h4>
            <ul class="nav list-group">

                    <li class="list-group-item">
                        <a class="icon-webcontent" href="#subsec_1_1">1.1 Titre 2</a>
                    </li>

                    <li class="list-group-item">
                        <a class="icon-comprehension" href="#subsec_1_2">1.2 Compréhension</a>
                    </li>

                    <li class="list-group-item">
                        <a class="icon-activite" href="#subsec_1_3">1.3 Activité</a>
                    </li>

                    <li class="list-group-item">
                        <a class="icon-webcontent" href="#subsec_1_4">1.4 Cours</a>
                    </li>

                    <li class="list-group-item">
                        <a class="icon-webcontent" href="#subsec_1_5">1.5 Titre 22</a>
                    </li>

            </ul>
        </li>

        <!-- Stop ici un item déployable -->
        <!-- Link to Annexe  -->
        <div class="annex-sep"></div>
        <li class="panel panel-default">
            <h4 class="panel-title">
                <a href="#sec_A">
                    <span class="sec-num icon-cc"></span>
                    <span class="sec-title">Réutiliser ce module</span>
                </a>
            </h4>
            <ul class="nav list-group">
                <li class="list-group-item" style="display:none">
                    <a class="icon" href="#subsec_A1"></a>
                </li>
            </ul>
        </li>
    </ul>
    <!--  bouton chevron "gauche" pour replier menu gauche-->
    <button type="button" class="navmenu-fixed-left navmenu-fixed-left navbar-offcanvas-toggle menugauchebtn collapsed hidden-md hidden-lg" data-toggle="offcanvas"  data-canvas="div.content" data-target="#menugauche"  id="menugauche-sm-left">
    	<span class="icon-chevron-left"> </span>
    </button>
</div>
<!-- Fin menu gauche classique -->

<div id="content">
    <!--  bouton chevron "droit" pour déplier menu gauche-->
    <button type="button" class="navmenu-fixed-left navmenu-fixed-left navbar-offcanvas-toggle menugauchebtn collapsed hidden-md hidden-lg" data-toggle="offcanvas"  data-canvas="div.content" data-target="#menugauche"  id="menugauche-sm">
	       <span class="icon-chevron-right"> </span>
    </button>
    <!-- Margin top 4 em -->
    <!-- Début contenu droite -->
    <ol class="breadcrumb">
        <li>
            <a href="#">
                <span class="icon-home"></span>
            </a>
        </li>
        <li><a href="#">Titre</a></li>
        <li class="active">Cours</li>
    </ol>

    <div class="contenudroite">


            <section  id="sec_1">
            <h1 class="icon-section title blue">1. Titre 1</h1>

                    <section id="subsec_1_1">
                        <h2 class="icon-webcontent title">1.1. Titre 2</h2>



                        <!-- teaser: first 5 lines -->
    					<div class="collapse hidden-text">
                            <span data-toggle="collapse" data-target="#subsec_1_1 .hidden-text" class="icon-minus-circled teaser-button"><i>(Réduire le cours)</i></span>

                            <span data-toggle="collapse" data-target="#subsec_1_1 .hidden-text" class="icon-minus-circled teaser-button"><i>(Réduire le cours)</i></span>
    					</div>
                                <!--  -->
                        <div class="teaser" data-toggle="collapse" data-target="#subsec_1_1 .hidden-text">
                            <span  class="icon-plus-circled teaser-button"><i>(Montrer la suite)</i></span>
                            <div class="tease"></div>

                        </div>
                        <!-- rest with a collapse -->

                </section>

                    <section id="subsec_1_2">
                        <h2 class="icon-comprehension title">1.2. Compréhension</h2>





                </section>

                    <section id="subsec_1_3">
                        <h2 class="icon-activite title">1.3. Activité</h2>





                </section>

                    <section id="subsec_1_4">
                        <h2 class="icon-webcontent title">1.4. Cours</h2>



                        <!-- teaser: first 5 lines -->
    					<div class="collapse hidden-text">
                            <span data-toggle="collapse" data-target="#subsec_1_4 .hidden-text" class="icon-minus-circled teaser-button"><i>(Réduire le cours)</i></span>

                            <span data-toggle="collapse" data-target="#subsec_1_4 .hidden-text" class="icon-minus-circled teaser-button"><i>(Réduire le cours)</i></span>
    					</div>
                                <!--  -->
                        <div class="teaser" data-toggle="collapse" data-target="#subsec_1_4 .hidden-text">
                            <span  class="icon-plus-circled teaser-button"><i>(Montrer la suite)</i></span>
                            <div class="tease"></div>

                        </div>
                        <!-- rest with a collapse -->

                </section>

                    <section id="subsec_1_5">
                        <h2 class="icon-webcontent title">1.5. Titre 22</h2>



                        <!-- teaser: first 5 lines -->
    					<div class="collapse hidden-text">
                            <span data-toggle="collapse" data-target="#subsec_1_5 .hidden-text" class="icon-minus-circled teaser-button"><i>(Réduire le cours)</i></span>

                            <span data-toggle="collapse" data-target="#subsec_1_5 .hidden-text" class="icon-minus-circled teaser-button"><i>(Réduire le cours)</i></span>
    					</div>
                                <!--  -->
                        <div class="teaser" data-toggle="collapse" data-target="#subsec_1_5 .hidden-text">
                            <span  class="icon-plus-circled teaser-button"><i>(Montrer la suite)</i></span>
                            <div class="tease"></div>

                        </div>
                        <!-- rest with a collapse -->

                </section>

        </section>

        <!-- download section here -->
        <section  id="sec_A">
            <h1 class="icon-section title blue">Annexe : réutiliser ce module</h1>


        </section>

    </div>
    <!-- Fin contenu droite -->

</div>
<!--Content -->""".strip() in module_html_content.strip())


# Main
if __name__ == '__main__':
    unittest.main(verbosity=1)
