#**************************************************************************
# Copyright (c) 2012 Digi International Inc.,
# All rights not expressly granted are reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Digi International Inc. 11001 Bren Road East, Minnetonka, MN 55343
#
#**************************************************************************

from __future__ import print_function

from google.appengine.ext.webapp import template
import webapp2

import json
import os

import lgn_client
from base import version_string, BaseHandler, login_required

#####
# Internal functions which implement account-y functionality


def change_password(old_password, new_password):
    '''Changes the account password.'''

    response = lgn_client.change_password(old_password, new_password)
    return response


def get_security_questions(username):
    '''
    Return the three security questions (with None's for unset questions).

    '''
    questions = lgn_client.get_security_questions(username)
    questionVO = questions.securityQuestionVO

    return [questionVO.reminderQuestion1, questionVO.reminderQuestion2,
            questionVO.reminderQuestion3]


def set_security_questions(username, security_questions):
    '''Set the three security questions (None to unset).'''
    qa1 = security_questions['question1'], security_questions['answer1']
    qa2 = security_questions['question2'], security_questions['answer2']
    qa3 = security_questions['question3'], security_questions['answer3']

    return lgn_client.create_security_question(qa1[1], qa2[1], qa3[1],
                                               qa1[0], qa2[0], qa3[0],
                                               username)


def reset_password(username, new_password, security_questions):
    '''Set the three security questions (None to unset).'''
    qa1 = security_questions['question1'], security_questions['answer1']
    qa2 = security_questions['question2'], security_questions['answer2']
    qa3 = security_questions['question3'], security_questions['answer3']

    return lgn_client.reset_password(new_password, qa1[1], qa2[1], qa3[1],
                                     qa1[0], qa2[0], qa3[0], username)

#####
# Web services handlers


class AccountHandler(BaseHandler):
    @login_required()
    def accountPage(self):
        self.response.out.write(
            template.render(
                os.path.join('template', 'account_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def changePassword(self):
        old_password = self.request.get('old_password')
        new_password = self.request.get('new_password')

        response = change_password(old_password, new_password)
        success = (response.code == '200')

        if success:
            # Update the current password to the new password
            self.session['password'] = new_password
        self.response.out.write(
            json.dumps({'logged_in': True, 'payload': success,
                        'message': str(response)}))

    @login_required(json_=True)
    def getSecurityQuestions(self):
        questions = get_security_questions(self.session.get('username'))
        keys = ['question_1', 'question_2', 'question_3']
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': dict(zip(keys, questions))}))

    @login_required(json_=True)
    def setSecurityQuestions(self):
        questions = {}

        questions['question1'] = self.request.get('question_1')
        questions['answer1'] = self.request.get('answer_1')

        questions['question2'] = self.request.get('question_2')
        questions['answer2'] = self.request.get('answer_2')

        questions['question3'] = self.request.get('question_3')
        questions['answer3'] = self.request.get('answer_3')

        response = set_security_questions(self.session.get('username'),
                                          questions)
        success = (response.code == '200')

        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': success,
                        'message': str(response)}))

    @login_required(json_=True)
    def resetPassword(self):
        new_password = self.request.get('new_password')

        questions = {}

        questions['question1'] = self.request.get('question_1')
        questions['answer1'] = self.request.get('answer_1')

        questions['question2'] = self.request.get('question_2')
        questions['answer2'] = self.request.get('answer_2')

        questions['question3'] = self.request.get('question_3')
        questions['answer3'] = self.request.get('answer_3')

        response = reset_password(
            self.session.get('username'), new_password, questions)
        success = (response.code == '200')

        self.response.out.write(
            json.dumps({'logged_in': True,
                        'message': str(response),
                        'payload': success}))

# Exported routes
account_routes = [
    webapp2.Route(r'/', AccountHandler, handler_method='accountPage',
                  methods=['GET']),
    webapp2.Route(r'/security/password', AccountHandler,
                  handler_method='changePassword',
                  methods=['POST', 'PUT']),
    webapp2.Route(r'/security/question', AccountHandler,
                  handler_method='getSecurityQuestions', methods=['GET']),
    webapp2.Route(r'/security/question', AccountHandler,
                  handler_method='setSecurityQuestions',
                  methods=['POST', 'PUT']),
    webapp2.Route(r'/security/reset', AccountHandler,
                  handler_method='resetPassword', methods=['PUT', 'POST']),
]
