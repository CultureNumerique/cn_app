# -*- coding: utf-8 -*-

import yattag
import logging
import random
import re
import markdown
from pygiftparser import parser as pygift

_ = pygift.i18n.language.gettext

MARKDOWN_EXT = ['markdown.extensions.extra', 'superscript']


"""
    This module add methods to the module pygiftparser with a monkey patch
    For this project, if you want to rewrite method, write your new method
    in this file like:

    >>> def myNewMethod(param1, param2):
        >>> code

    >>> pygift.newMethod = myNewMethod

    If you want add a Class method :

    >>> def myNewMethod(self, param1, param2):
        >>> code

    >>> pygift.[class_name].newMethod = myNewMethod

    for apply patch, import pygift and fromGift in your file.

"""


def mdToHtml(text, doc=None):
    """
    Transform txt in markdown to html

    :param doc: yattag.doc()

    :return: HTML text
    :rtype: String

    """
    if not (text.isspace()):
        # text = re.sub(r'\\n','\n',text)
        html_text = markdown.markdown(text, MARKDOWN_EXT,
                                      output_format='xhtml')
        text = re.sub(r'\\n', '\n', text)
        if doc:
            doc.asis(html_text)
            doc.text(' ')
            return
        else:
            return html_text


# ######################################
# ##           Question               ##
# ######################################

def toEDX(self):
    """
    produces an XML fragment for EDX, use toEDX from AnswerSet

    :return: The doc value of XML text problem
    :rtype: String
    """
    if not self.valid:
        logging.warning(pygift.INVALID_FORMAT_QUESTION)
        return ''
    return self.answers.toEDX()


pygift.Question.toEDX = toEDX

# ######################################
# ##             Answer               ##
# ######################################

# #############
# ##AnswerSet##
# #############
pygift.AnswerSet.cc_profile = 'ESSAY'
pygift.AnswerSet.max_att = '1'
#Fixed maximal essay to 1 in EDX and Moodle, change this attribut if you want more


# IMS
def aslistInteractionsIMS(self, doc, tag, text):
    """
    return the list interactions in IMS form the class Answer
    (example : When someone have the good answer, or the bad.)
    Add XML in the yattag.doc
    """
    pass


pygift.AnswerSet.listInteractionsIMS = aslistInteractionsIMS


def aspossiblesAnswersIMS(self, doc, tag, text, rcardinality='Single'):
    """
    Return the list of possible responses, example for
    SelectSet(unique good answer) and
    MultipleChoicesSet (one or many good answer(s)).

    :param rcardinality: represent number of good answer(s)
    :type rcardinality: String
    """
    with doc.tag('response_str', rcardinality=rcardinality,
                 ident='response_'+str(self.question.id)):
        doc.stag('render_fib', rows=5, prompt='Box', fibtype="String")


pygift.AnswerSet.possiblesAnswersIMS = aspossiblesAnswersIMS


def astoIMSFB(self, doc, tag, text):
    """
    return the feedback for each answer.
    """
    pass


pygift.AnswerSet.toIMSFB = astoIMSFB


# EDX
def astoEDX(self):
    """
    transform object question in XML problem for EDX,
    depends to Answer type

    :return: The doc value of XML text problem
    :rtype: String
    """
    doc = yattag.Doc()
    with doc.tag("problem", display_name=self.question.title,
                 max_attempts=self.max_att):
        with doc.tag("legend"):
            mdToHtml(self.question.text, doc)
        self.scriptEDX(doc)
        self.ownEDX(doc)
        # FIXME : Ajouter un warning ici si rien n'est renvoyé
        if (len(self.question.generalFeedback) > 1):
            with doc.tag("solution"):
                with doc.tag("div", klass="detailed-solution"):
                    mdToHtml(self.question.generalFeedback, doc)
    return doc.getvalue()


pygift.AnswerSet.toEDX = astoEDX


def asownEDX(self, doc):
    """
    Transforms the answers into XML EDX according to their type
    """
    pass


pygift.AnswerSet.ownEDX = asownEDX


def asscriptEDX(self, doc):
    """
    In EDX, we can add a python or javascript script.
    This method allow to add script in XML EDX.
    """
    pass


pygift.AnswerSet.scriptEDX = asscriptEDX


# #########
# ##Essay##
# #########
# pygift.Essay.max_att = ''


def escriptEDX(self, doc):
    with doc.tag("script", type="loncapa/python"):
        doc.text("""import re
def checkAnswerEssay(expect, ans):
    response = re.search('', ans)
    if response:
        return 1
    else:
        return 0
            """)
    doc.asis('<span id="'+str(self.question.id)+'"></span>')
    with doc.tag("script", type="text/javascript"):
        doc.asis("""
    /* The object here is to replace the single line input with a textarea */
    (function() {
    var elem = $("#"""+str(self.question.id)+"""")
        .closest("div.problem")
        .find(":text");
    /* There's CSS in the LMS that controls the height,
    so we have to override here */
    var textarea = $('<textarea style="height:150px" rows="20" cols="70"/>');
    console.log(elem);
    console.log(textarea);
    //This is just a way to do an iterator in JS
    for (attrib in {'id':null, 'name':null}) {
        textarea.attr(attrib, elem.attr(attrib));
    }
    /* copy over the submitted value */
    textarea.val(elem.val())
    elem.replaceWith(textarea);

    })();
            """)


pygift.Essay.scriptEDX = escriptEDX


def eownEDX(self, doc):
    with doc.tag("customresponse", cfn="checkAnswerEssay"):
        doc.asis('<textline size="40" correct_answer="" label="Problem Text"/>')


pygift.Essay.ownEDX = eownEDX

# ###############
# ##Description##
# ###############
pygift.Description.cc_profile = 'DESCRIPTION'

# ################
# ##TrueFalseSet##
# ################
pygift.TrueFalseSet.cc_profile = 'TRUEFALSE'


def tfsownEDX(self, doc):
    with doc.tag("multiplechoiceresponse"):
        with doc.tag("choicegroup", type="MultipleChoice"):
            if self.answer:
                correct = 'true'
                wrong = 'false'
            else:
                correct = 'false'
                wrong = 'true'
            with doc.tag("choice", correct=correct):
                doc.text(_('True'))
                if correct == 'true':
                    doc.asis("<choicehint>" +
                             self.feedbackCorrect +
                             "</choicehint>")
                else:
                    doc.asis("<choicehint>"+self.feedbackWrong+"</choicehint>")
            with doc.tag("choice", correct=wrong):
                doc.text(_('False'))
                if wrong == 'true':
                    doc.asis("<choicehint>" +
                             self.feedbackCorrect +
                             "</choicehint>")
                else:
                    doc.asis("<choicehint>"+self.feedbackWrong+"</choicehint>")


pygift.TrueFalseSet.ownEDX = tfsownEDX


def tfspossiblesAnswersIMS(self, doc, tag, text):
    with tag('response_lid', rcardinality='Single',
             ident='response_'+str(self.question.id)):
        with tag('render_choice', shuffle='No'):
            with tag('response_label',
                     ident='answer_'+str(self.question.id)+'_'+'0'):
                with tag('material'):
                    with tag('mattext', texttype="text/html"):
                        text(_('True'))
            with tag('response_label',
                     ident='answer_'+str(self.question.id)+'_'+'1'):
                with tag('material'):
                    with tag('mattext', texttype="text/html"):
                        text(_('False'))


pygift.TrueFalseSet.possiblesAnswersIMS = tfspossiblesAnswersIMS


def tfslistInteractionsIMS(self, doc, tag, text):
    if self.answer:
        title1 = 'Correct'
        score1 = 100
        title2 = ''
        score2 = 0
    else:
        title1 = ''
        score1 = 0
        title2 = 'Correct'
        score2 = 100
    with tag('respcondition', title=title1):
        with tag('conditionvar'):
            # respident is id of response_lid element
            with tag('varequal',
                     respident='response_'+str(self.question.id)):
                text('answer_'+str(self.question.id)+'_0')
        with tag('setvar', varname='SCORE', action='Set'):
            text(score1)
        doc.stag('displayfeedback',
                 feedbacktype='Response',
                 linkrefid='feedb_0')
    with tag('respcondition', title=title2):
        with tag('conditionvar'):
            with tag('varequal',
                     respident='response_'+str(self.question.id)):
                text('answer_'+str(self.question.id)+'_1')
        with tag('setvar', varname='SCORE', action='Set'):
            text(score2)
        doc.stag('displayfeedback',
                 feedbacktype='Response',
                 linkrefid='feedb_1')


pygift.TrueFalseSet.listInteractionsIMS = tfslistInteractionsIMS


# ####################
# ##NumericAnswerSet##
# ####################
def nasownEDX(self, doc):
    # FIXME : Problème pour le multi answer NUMERIC,
    # ne gère qu'une réponse
    correctAnswer = []
    for a in self.answers:
        if a.fraction > 0:
            correctAnswer.append(a)
    if len(correctAnswer) == 0:
        logging.warning('')
        return
    elif len(correctAnswer) == 1:
        correctAnswer[0].ownEDX(doc)


pygift.NumericAnswerSet.ownEDX = nasownEDX


# ###############
# ##MatchingSet##
# ###############
pygift.MatchingSet.cc_profile = 'ESSAY'  # need in toIMS.py


def msownEDX(self, doc):
    for a in self.answers:
        with doc.tag('h2'):
            doc.text(a.question+" ")
        with doc.tag('optionresponse'):
            options = '\"('
            random.shuffle(self.possibleAnswers)
            for a2 in self.possibleAnswers:
                options += "'"+a2+"'"+','
            options += ')\"'
            doc.asis("<optioninput label=\"" + a.question + "\" options=" +
                     options + "  correct=\"" + a.answer+"\" ></optioninput>")


pygift.MatchingSet.ownEDX = msownEDX


# ##############
# ##ChoicesSet##
# ##############

# #IMS
def cslistInteractionsIMS(self, doc, tag, text):
    for id_a, answer in enumerate(self.answers):
        score = 0
        if answer.fraction == 100:
            title = 'Correct'
            score = 100
        else:
            title = ''
            score = answer.fraction
        with tag('respcondition', title=title):
            with tag('conditionvar'):
                # respident is id of response_lid element
                with tag('varequal',
                         respident='response_' + str(self.question.id)):
                    text('answer_'+str(self.question.id)+'_'+str(id_a))
            with tag('setvar', varname='SCORE', action='Set'):
                text(score)
            doc.stag('displayfeedback',
                     feedbacktype='Response',
                     linkrefid='feedb_'+str(id_a))


pygift.ChoicesSet.listInteractionsIMS = cslistInteractionsIMS


def cspossiblesAnswersIMS(self, doc, tag, text, rcardinality='Single'):
    with tag('response_lid',
             rcardinality=rcardinality,
             ident='response_' + str(self.question.id)):
        with tag('render_choice', shuffle='No'):
            for id_a, answer in enumerate(self.answers):
                with tag('response_label',
                         ident='answer_'+str(self.question.id) +
                         '_'+str(id_a)):
                    with tag('material'):
                        with tag('mattext', texttype="text/html"):
                            text(pygift.markupRendering(answer.answer,
                                                        self.question.markup))


pygift.ChoicesSet.possibleAnswersIMS = cspossiblesAnswersIMS


def cstoIMSFB(self, doc, tag, text):
    for id_a, answer in enumerate(self.answers):
        with tag('itemfeedback', ident='feedb_'+str(id_a)):
            with tag('flow_mat'):
                with tag('material'):
                    with tag('mattext', texttype='text/html'):
                        if answer.feedback:
                            text(pygift.markupRendering(answer.feedback,
                                                        self.question.markup))
                        else:
                            text('')


pygift.ChoicesSet.toIMSFB = cstoIMSFB


# ############
# ##ShortSet##
# ############
pygift.ShortSet.cc_profile = 'MISSINGWORD'


def shortsownEDX(self, doc):
    with doc.tag('stringresponse',
                 answer=self.answers[0].answer,
                 type='ci'):
        if len(self.answers) > 1:
            for i, a in enumerate(self.answers):
                if i > 0:
                    doc.asis('<additional_answer answer="' +
                             a.answer +
                             '"></additional_answer>')
        doc.asis("<textline size='20' />")


pygift.ShortSet.ownEDX = shortsownEDX


# #############
# ##SelectSet##
# #############
pygift.SelectSet.cc_profile = 'MULTICHOICE'


def ssownEDX(self, doc):
    with doc.tag("multiplechoiceresponse"):
        with doc.tag("choicegroup", type="MultipleChoice"):
            for a in self.answers:
                if a.fraction > 0:
                    korrect = 'true'
                else:
                    korrect = 'false'
                with doc.tag("choice", correct=korrect):
                    doc.text(a.answer)
                    if (a.feedback) and (len(a.feedback) > 1):
                        doc.asis("<choicehint>"+a.feedback+"</choicehint>")


pygift.SelectSet.ownEDX = ssownEDX

# def sspossiblesAnswersIMS(self,doc,tag,text):
#     cspossiblesAnswersIMS(self,doc,tag,text)

pygift.SelectSet.possiblesAnswersIMS = cspossiblesAnswersIMS


# #########################
# ##  MultipleChoicesSet ##
# #########################
pygift.MultipleChoicesSet.cc_profile = 'MULTIANSWER'


def mcsetownEDX(self, doc):
    with doc.tag("choiceresponse", partial_credit="EDC"):
        with doc.tag("checkboxgroup"):
            for a in self.answers:
                if a.fraction > 0:
                    korrect = 'true'
                else:
                    korrect = 'false'
                with doc.tag("choice", correct=korrect):
                    doc.text(a.answer)
                    if (a.feedback) and (len(a.feedback) > 1):
                        with doc.tag("choicehint", selected="true"):
                            doc.text(a.answer+" : "+a.feedback)


pygift.MultipleChoicesSet.ownEDX = mcsetownEDX


def mcspossiblesAnswersIMS(self, doc, tag, text):
    cspossiblesAnswersIMS(self, doc, tag, text, 'Multiple')


pygift.MultipleChoicesSet.possiblesAnswersIMS = mcspossiblesAnswersIMS


def mcslistInteractionsIMS(self, doc, tag, text):
    with tag('respcondition', title="Correct", kontinue='No'):
        with tag('conditionvar'):
            with tag('and'):
                for id_a, answer in enumerate(self.answers):
                    score = 0
                    try:
                        score = answer.fraction
                    except:
                        pass
                    if score <= 0:
                        with tag('not'):
                            with tag('varequal',
                                     case='Yes',
                                     respident='response_' +
                                     str(self.question.id)):
                                text('answer_'+str(self.question.id) +
                                     '_'+str(id_a))
                    else:
                        with tag('varequal',
                                 case='Yes',
                                 respident='response_' +
                                 str(self.question.id)):
                            text('answer_'+str(self.question.id)+'_'+str(id_a))
        with tag('setvar', varname='SCORE', action='Set'):
            text('100')
        doc.stag('displayfeedback',
                 feedbacktype='Response',
                 linkrefid='general_fb')
    for id_a, answer in enumerate(self.answers):
        with tag('respcondition', kontinue='No'):
            with tag('conditionvar'):
                with tag('varequal',
                         respident='response_'+str(self.question.id),
                         case="Yes"):
                    text('answer_'+str(self.question.id)+'_'+str(id_a))
            doc.stag('displayfeedback',
                     feedbacktype='Response',
                     linkrefid='feedb_'+str(id_a))


pygift.MultipleChoicesSet.listInteractionsIMS = mcslistInteractionsIMS


# #######################
# ##NumericAnswerMinMax##
# #######################
def numMinMaxownEDX(self, doc):
    with doc.tag('numericalresponse',
                 answer="["+str(self.mini) +
                 "," +
                 str(self.maxi)+"]"):
        doc.asis("<formulaequationinput />")


pygift.NumericAnswerMinMax.ownEDX = numMinMaxownEDX


# #################
# ##NumericAnswer##
# #################
def naownEDX(self, doc):
        with doc.tag('numericalresponse',
                     answer=str(self.value)):
            if self.tolerance != 0.0:
                doc.asis("<responseparam type='tolerance' default='" +
                         str(self.tolerance)+"' />")
            doc.asis("<formulaequationinput />")


pygift.NumericAnswer.ownEDX = naownEDX
