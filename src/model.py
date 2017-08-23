# -*- coding: utf-8 -*-
#
# #####################################################################################
#
#    Data model for Courses and Activities. The module provides
#    parse tools for markdown files following the
#    Culture Numérique guidelines. Outputs
#       - JSON config file
#       - HTML files (a cut out of the file in html and gift files,
#                     orderered in a folder structure)
#       - HTML views
#       - IMSCC archive (Open EDX coming soon)
#
# #####################################################################################


import sys
import re
import json
import markdown
import yattag

import logging
from inspect import isclass

from slugify import slugify

from pygiftparser import parser as pygift
import fromGift  # seems unused but used for the mondey patching

import toIMS
import toEDX
import utils
import os.path


from cnSettings import MARKDOWN_EXT, VIDEO_THUMB_API_URL, DEFAULT_VIDEO_THUMB_URL, DEFAULT_BASE_URL


# Regexps
reEndHead = re.compile('^#\s.+$')
reStartSection = re.compile('^#\s+(?P<title>.*)$')
reStartSubsection = re.compile('^##\s+(?P<title>.*)$')
reStartActivity = re.compile('^```(?P<type>.*)$')
reEndActivity = re.compile('^```\s*$')
reMetaData = re.compile('^(?P<meta>([A-Z])+?):\s*(?P<value>.*)\s*$')
reVideosLink  = re.compile('^\[(?P<video_title>.*)\]\s*\((?P<video_link>.*)\){:\s*\.cours_video\s*.*}', flags=re.M)

# Warning messages
DEFAULT_PLACEMENT_BODY = "[UTIL]Ce fragment de texte n'a été placé dans aucune sous-section, placement automatique dans une sous-section \"Cours\": "
METADATA_NOT_FOUND = "[UTIL]Cette balise de Header ne correspond à aucun attribut modifiable, vérifier l'orthographe/l'existence de cette balise: "
NOT_START_SECTION = "[UTIL]Cette partie de texte qui suit le header n'est pas placée dans une section, mettez un \"# <titre>\" après l'en-tête: "

# Hiérarchie
hierarchie = ''


def goodActivity(match):
    """ utility function used with 'reStartActivity'
    regex pattern to determine wether the 'type' variable
    of the given matched pattern fits the name of class defined in this module

    :param match: result of reStartActivity.match(some_parsed_line)
          (see Regex expressions defined above)
    :type match: re.MatchObject
     """
    m = sys.modules[__name__]
    t = match.group('type').decode('UTF-8').replace('é', 'e').title()
    typeSection = re.sub('[ ._-]',
                         '',
                         t)
    if typeSection in m.__dict__:
        act = getattr(m, typeSection)
        if isclass(act):
            return act
    return None


class ComplexEncoder(json.JSONEncoder):
    """Encoder for Json serialization: just delete recursive
structures. Used in toJson instance methods"""
    def default(self, obj):
        if isinstance(obj, Section) or isinstance(obj, Module):
            return obj.__dict__
        elif isinstance(obj, Subsection):
            d = obj.__dict__.copy()
            del d['section']
            if isinstance(obj, AnyActivity):
                del d['questions']
            return d
        return json.JSONEncoder.default(self, obj)


class Subsection:
    """
    Abstract class for any type of subsection: lectures and activities

    :param section: section object to which this subsection belongs
    :type section: Section object

    """
    num = 1  # class-wise instance counter

    def __init__(self, section):
        self.section = section
        # mere string for display the subsection number
        self.num = self.section.num+'-'+str(Subsection.num)
        self.videos = []
        self.medias = []
        Subsection.num += 1

    def getFilename(self, term='html'):
        """returns the filename associated to this subsection

        :param term: termination of the file ('html' or 'xml')
        :type term: string

         """
        self.filename = slugify(self.num+self.title)+'_'+self.folder+'.'+term
        return self.filename

    def toGift(self):
        return ''

    def toXMLMoodle(self):
        pass

    def absolutizeMediaLinks(self):
        """ returns the instance src attribute (i.e the bit of source
            code corresponding to this subsection) modified so that relative
            media links are turned absolute with the base_url
            and the module name
        """
        self.src = re.sub('\]\(\s*(\.\/)*\s*media/',
                          '](' +
                          self.section.base_url + '/' +
                          self.section.module_name + '/media/',
                          self.src)

    def rebaseMediaLinks(self, dest):
        """ changes the media links in the html_src code to a new link
        /<modulename>/media/ is converted into dest
        """
        return re.sub(re.escape('/'+self.section.module_name+'/media/'),
                      dest,
                      self.html_src)

    def parseMediaLinks(self):
        """Parse instance src  and search for video matches.
           In case of a match, creates a video object and assign
           it to self.videos list attribute.

           returns True if the number of videos found is above 0,
                   False otherwise"""
        media_findall = re.findall('/media/(?P<media_name>.*)\)',
                                   self.src,
                                   flags=re.M)
        for (i, media_match) in enumerate(media_findall):
            new_media = {
                'media_name': media_match,
                'media_id': 'img'+self.num+str(i)
            }
            self.medias.append(new_media)
        return (len(media_findall) > 0)


class Cours(Subsection):
    """ Class for a lecture.
        If src is not empty and no file is given, then this means
        that the content has already been parsed in Section.parse().
        Else if a file pointer is given and param 'src' is empty,
        this means that Section.parse() has detected a new 'Cours'
        instance that we keep on parsing here.

        :param section: containing section object
                        (to be deleted in JSON representation,
                        see ComplexEncoder class)
        :type section: Section object

        :param file: parsed file (default None)
        :type file: File pointer

        :param src: text string with source of the parsed subsection
                    (default: empty string)

        :param title: text string that gives the Cours title
                      (default 'Cours')
    """

    def __init__(self, section, file=None, src='', title='Cours'):
        Subsection.__init__(self, section)
        self.title = title
        self.folder = 'webcontent'
        if src:
            # case when the content has already been parsed
            self.src = src
        else:
            # case when only the begining of a Course has been
            # detected, so we resume the parsing here
            self.src = ''
            self.parse(file)
        self.parseVideoLinks()
        self.absolutizeMediaLinks()
        self.parseMediaLinks()

    def parse(self, f):
        """Read lines in file pointer 'f' until:

            - start of a new section
            - start of another subsection
            - start of a new (checked) activity
        """
        self.lastLine = f.readline()
        while self.lastLine and not reStartSection.match(self.lastLine) and not reStartSubsection.match(self.lastLine) :
            # Is it really the end of the section?
            # blocks that are not activities are included!
            match = reStartActivity.match(self.lastLine)
            if match and goodActivity(match):
                return
            self.src += self.lastLine
            self.lastLine = f.readline()

    def toHTML(self, feedback_option=False):
        """Assign and return the html_src attribute,
        i.e the html representation of this Course subsection

        :param feedback_option: determines wether or not it must
                include feedback and correct answer (default False)
        """
        self.html_src = markdown.markdown(self.src, MARKDOWN_EXT)
        self.html_src = utils.iframize_video_anchors(self.html_src,
                                                     'lien_video')
        self.html_src = utils.add_target_blank(self.html_src)
        return self.html_src

    def parseVideoLinks(self):
        """Parse instance src  and search for video matches.
        In case of a match, creates a video object and assign
        it to self.videos list attribute.
        return True if the number of videos found is above 0,
               False otherwise"""
        videos_findall = reVideosLink.findall(self.src)
        for video_match in videos_findall:
            new_video = {
                'video_title': video_match[0],
                'video_link': video_match[1].strip(),
                'video_src_link': utils.get_video_src(video_match[1].strip()),
                'video_thumbnail': DEFAULT_VIDEO_THUMB_URL
            }
            self.videos.append(new_video)
        return (len(videos_findall) > 0)

    def videoIframeList(self):
        """Generates and returns a text string containing all
           the iframe codes for a course subsection"""
        video_list = "\n"+self.num+' '+self.title+'\n'
        for v in self.videos:
            video_list += '<iframe src='+v['video_src_link']+' width="500" height="281" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>\n'
        return video_list


class AnyActivity(Subsection):
    """Abstract class for any activity.
       Responsible for parsing questions from the gift code in src attribute

    :param section:  containing section object (to be deleted in
                     JSON representation, see ComplexEncoder class)
    :type section: Section object

    :param file:  parsed file (default None)
    :type file: File pointer
    """
    def __init__(self, section, f):
        Subsection.__init__(self, section)
        self.src = ''
        self.parse(f)
        self.absolutizeMediaLinks()
        # need to transform String in File pointer with iter function
        self.questions = pygift.parseFile(iter(self.src.splitlines(True)))
        self.parseMediaLinks()

    def parse(self, f):
        """Read lines in file pointer f until the end of the activity"""
        self.lastLine = f.readline()
        while self.lastLine and not reEndActivity.match(self.lastLine):
            self.src += self.lastLine
            self.lastLine = f.readline()

    def toGift(self):
        """Returns a text string containing the gift code
           of all the questions of this AnyActivity instance"""
        gift_src = ''
        for question in self.questions:
            gift_src += '\n'+question.source+'\n'
        return gift_src

    def toHTML(self, feedback_option=False):
        """Assign and return the html_src attribute,
           i.e. the concatenation of the HTML representation
           of all questions of this activity.

        :param feedback_option: wether or not output should
              include feedbacks to the questions of the activity
        :type feedback_option: Boolean

        :rtype: text string with html code
        """
        self.html_src = ''
        d = yattag.Doc()
        for q in self.questions:
            # append each question to html output
            q.toHTML(d, feedbacks=feedback_option)
        self.html_src = utils.add_target_blank(d.getvalue())
        return self.html_src

    def toEdxProblemsList(self):
        """Returns xml source code of all the questions in
           EDX XML format. *depends on toEdx.py module*

        :rtype: texte string of xml code
        """
        edx_xml_problem_list = ""
        for question in self.questions:
            edx_xml_problem_list += '\n'+question.toEDX()+'\n'
        return edx_xml_problem_list

    def toXMLMoodle(self):
        """Returns the XML representation following IMS QTI
        standard of all the questions in this activity.
        *depends on toIMS.py module*

        :rtype: texte string of xml code
        """
        # a) depending on the type, get max number of attempts for the test
        # FIXME : It is usefull?
        # if isinstance(self, Comprehension):
        #     max_attempts = '1'
        # else:
        #     max_attempts = 'unlimited'
        # b) write empty xml test file for moodle export
        return toIMS.create_ims_test(self.questions,
                                     self.num+'_'+slugify(self.title),
                                     self.title)


class Comprehension(AnyActivity):
    """Subclass of AnyActivity defining a 'compréhension' type of activity"""
    actnum = 0  # specific counter for this subclass of AnyActivity

    def __init__(self, section, src):
        AnyActivity.__init__(self, section, src)
        self.title = 'Compréhension'
        self.folder = 'Comprehension'
        Comprehension.actnum += 1


class Activite(AnyActivity):
    """Subclass of AnyActivity defining a simple 'activité' type of activity"""
    actnum = 0  # specific counter for this subclass of AnyActivity

    def __init__(self, section, src):
        AnyActivity.__init__(self, section, src)
        self.title = 'Activité'
        self.folder = 'Activite'
        Activite.actnum += 1


class ActiviteAvancee(AnyActivity):
    """Subclass of AnyActivity defining an 'activité avancée'
    type of activity"""
    actnum = 0  # specific counter for this subclass of AnyActivity

    def __init__(self, section, src):
        AnyActivity.__init__(self, section, src)
        self.title = 'Activité avancée'
        self.folder = 'ActiviteAvancee'
        ActiviteAvancee.actnum += 1


class Section:
    """Class defining the section level in the course module model of Esc@pad

    :param  title:  text string title
    :type title: string

    :param  f:  module source file pointer
    :type f: File

    :param  module_name:  text string of the module name
    :type module_name: string

    :param  base_url:  base url for building absolute paths
                       for relative media
                       (default: DEFAULT_BASE_URL defined in model.py)
    :type base_url: string
    """
    num = 1

    def __init__(self, title, f, module_name, base_url=DEFAULT_BASE_URL):
        self.title = title
        self.subsections = []
        self.num = str(Section.num)
        self.module_name = module_name
        self.base_url = base_url
        self.parse(f)
        Section.num += 1
        Subsection.num = 1

    def build_default_cours(self, text):
        """
        Build a default Cours with text without subsections

        :param body: Text which contains a part of class
        :type body: String
        """
        self.subsections.append(Cours(self, src=text))

    # FIXME : Beaucoup de if/else, changer les conditions & regrouper tout
    def parse(self, f):
        """Read lines in file pointer 'f' until the start of a new
        section. If the start of a new subsection or new activity is
        detected, parsing is continued in corresponding subsection
        parse method that returns the newly created object
        """
        body = ''
        self.lastLine = f.readline()
        while self.lastLine:
            # is it a new section ?
            match = reStartSection.match(self.lastLine)
            if match:
                # for sections with only text:
                if body and not body.isspace():
                    self.build_default_cours(body)
                    body = ''
                break
            else:
                # is it a new subsection ?
                match = reStartSubsection.match(self.lastLine)
                if match:
                    # should I create a subsection (text just below a section
                    # or between activities
                    if body and not body.isspace():
                        self.build_default_cours(body)
                        body = ''
                    # parsing is then continued in Cours parse method,
                    sub = Cours(self, file=f, title=match.group('title'))
                    self.subsections.append(sub)
                    # The next line is the last line read in the parse
                    # of the subsection
                    self.lastLine = sub.lastLine
                    body = ''
                else:
                    # is it an activity
                    match = reStartActivity.match(self.lastLine)
                    if match:
                        act = goodActivity(match)
                        if act:
                            # should I create a subsection (text just
                            # below a section or between activities
                            if body and not body.isspace():
                                self.build_default_cours(body)
                                body = ''
                            self.subsections.append(act(self, f))
                            # read a new line after the end of blocks
                        else:
                            logging.warning("Type d'activité inconnu %s",
                                            self.lastLine)
                            body += self.lastLine
                    else:
                        # no match, add the line to the body and read
                        # a new line
                        body += self.lastLine
                    self.lastLine = f.readline()
        # If lastLine is empty (file is ending), we write the body in
        # Cours Subsection
        if body and not body.isspace():
            self.build_default_cours(body)

    def toHTML(self, feedback_option=False):
        """Triggers the HTML output generation for all subsections. Does not
        return anything"""
        for sub in self.subsections:
            sub.toHTML(feedback_option)


    # # FIXME: is this usefull ??
    # def toCourseHTML(self):
    #     """Loops through Cours subsections only.
    #
    #     :rtype: a string concatenating subsections HTML output
    #     """
    #     courseHTML = ""
    #     for sub in self.subsections:
    #         if isinstance(sub, Cours):
    #             courseHTML += "\n\n<!-- Subsection "+sub.num+" -->\n"
    #             courseHTML += markdown.markdown(sub.src, MARKDOWN_EXT)
    #     return courseHTML

    def toGift(self):
        """Returns a concatenation (text string) of the GIFT source code of
        all questions of all activities in this section"""
        allGifts = ""
        for sub in self.subsections:
            if isinstance(sub, AnyActivity):
                # Add category here
                allGifts += "\n$CATEGORY: $course$/Quiz Bank '"+sub.num+' '+sub.title+"'\n\n"
                allGifts += sub.toGift()
        return allGifts

    def toVideoList(self):
        """Returns a text string containing all iframe code of all videos in
        this section"""
        video_list = ""
        for sub in self.subsections:
            if isinstance(sub, Cours) and len(sub.videos) > 0:
                video_list += sub.videoIframeList()
        return video_list

    def toCourseHTMLVisualisation(self):
        """Loops through Cours subsections only.

        :rtype: a string concatenating subsections HTML output
        """
        courseHTML = ""
        for sub in self.subsections:
            if isinstance(sub, Cours):
                courseHTML += "\n\n<!-- Subsection "+sub.num+" -->\n"
                courseHTML += "\n\n<h2>"+sub.num+". "+sub.title+" </h2>\n"
                courseHTML += markdown.markdown(sub.src, MARKDOWN_EXT)
        return courseHTML


class Module:
    """ Module structure.

    :param  f:  module source file pointer
    :type f: File

    :param name:  module name
    :type name: string

    :param  base_url:  the base url to build absolute media paths
                       (default to DEFAULT_BASE_URL)
    :type base_url: string

    """

    def __init__(self, f, name, base_url=DEFAULT_BASE_URL):
        self.sections = []
        Section.num = 1
        self.name = name
        self.ims_archive_path = ''
        self.language = 'fr'
        self.title = 'Titre long'
        self.menutitle = 'Titre'
        self.logo_filename = os.path.join('static', 'img', 'help.png')
        self.author = 'culture numerique'
        self.css = 'http://culturenumerique.univ-lille3.fr/css/base.css'
        self.base_url = base_url
        self.parse(f)
        self.act_counter = {c.__name__: c.actnum for c in [Comprehension,
                                                           Activite,
                                                           ActiviteAvancee]}

    def __del__(self):
        for c in [Comprehension, Activite, ActiviteAvancee]:
            c.actnum = 0

    def parseHead(self, f):
        """Called by module.parse() method. Captures meta-data within the
        first lines of the source file. Stops and return the first line
        starting with #, which means the start of the first section

        :param  f :  module source file pointer
        :type f: File

        :rtype: string, last line parsed

        """

        l = f.readline()

        while l and not reEndHead.match(l):
            m = reMetaData.match(l)
            if m:
                meta = m.group('meta').lower()
                value = m.group('value').strip()
                if not (meta in self.__dict__):
                    logging.warning(METADATA_NOT_FOUND + "%s", meta.upper())
                setattr(self, meta, value)
            elif (l != '\n'):
                logging.warning(NOT_START_SECTION + l)
            l = f.readline()

        return l

    def toJson(self):
        """Returns the JSON representation of the module object. Uses the
custom ComplexEncoder class"""
        return json.dumps(self,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '),
                          cls=ComplexEncoder)

    def parse(self, f):
        """Parse module source file, starting by the head to retrieve the
         meta-data. Read all the lines until the start of a new
         section (see reStartSection regex). In this case, parsing is
         continued in Section.parse() method that returns a new
         Section object and the last line parsed. Parsing goes on
         until that last line returned is not the start of a new
         Section.

        """
        l = self.parseHead(f)  # up to first section

        match = reStartSection.match(l)

        while l and match:
            s = Section(match.group('title'),
                        f,
                        self.name,
                        self.base_url)

            self.sections.append(s)
            l = s.lastLine
            match = reStartSection.match(l)
        # Si qqlch dans l and pas de match -> pas trouvé de section pour démarrer -> WARNING

    def toHTML(self, feedback_option=False):
        """triggers the generation of HTML output for all sections"""
        for s in self.sections:
            s.toHTML(feedback_option)

    def toGift(self):
        """ Returns a text string with all questions of all
            the activities of this modules object.
            Can be used for import a questions bank into moodle"""
        questions_bank = ""
        for s in self.sections:
            questions_bank += s.toGift()
        return questions_bank

    def toVideoList(self):
        """Returns a text string with all video iframe codes """
        video_list = ""
        for s in self.sections:
            video_list += s.toVideoList()+'\n\n'
        return video_list

    def toCourseHTMLVisualisation(self):
        """To CourseHTML with title (used for getting preview of the website)

        :rtype: Returns a string of the concatenation of their HTML output"""
        courseHTML = ""
        for sec in self.sections:
            courseHTML += "\n\n<!-- Section "+sec.num+" -->\n"
            courseHTML += "\n\n<h1> "+sec.num+". "+sec.title+" </h1>\n"
            courseHTML += sec.toCourseHTMLVisualisation()
        return courseHTML


class CourseProgram:
    """
        A course program is made of one or several course modules.
        A CP is initiated from a repository containing global
        paramaters file (logo.jpg, title.md, home.md)
        and folders moduleX containing module file and medias

        :param title: course title
        :type title: string

        :param repository: path to the folder containing the modules
        :type repository: string

    """
    def __init__(self, title, repository):
        self.modules = []
        self.repository = repository
        self.title = title
        self.logo_path = 'logo.png'
