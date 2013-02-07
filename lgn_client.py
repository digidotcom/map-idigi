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

import webapp2
from os import environ
import logging

from suds.client import Client
from suds.sax.element import Element

log = logging.getLogger(__name__)

wsdl_base = environ['MAP_WSDL_BASE']
log.info('wsdl_base: {}'.format(wsdl_base))

LGN_URL = '{}LoginService?wsdl'.format(wsdl_base)
log.info('login url {}'.format(LGN_URL))


def get_lgn_client():
    '''
    Returns a soap client object.

    If an object has already been created, we recyle it,
    otherwise, a new one is created and returned.

    '''
    app = webapp2.get_app()
    request = webapp2.get_request()

    username = request.registry['session'].get('username')
    password = request.registry['session'].get('password')
    lgn_key = 'lgn_client:{}'.format(username)

    # Check if we already have the client
    lgn_client = app.registry.get(lgn_key)

    if not lgn_client:
        lgn_client = Client(LGN_URL, cache=None)
        lgn_client.add_prefix(
            'srv', "http://service.login.core.mtrak.digi.com")
        lgn_client.add_prefix(
            'vo', "http://vo.login.core.mtrak.digi.com/xsd")

        app.registry[lgn_key] = lgn_client

    lgn_client.set_options(soapheaders=(
        Element('username').setText(username),
        Element('password').setText(password)))

    return lgn_client


def _make_VO(namespace, name, **kwargs):
    '''
    Creates a Suds SOAP value object.

    namespace = string
    name = string

    '''
    lgn_client = get_lgn_client()
    vo_str = namespace + ':' + name
    vo = lgn_client.factory.create(vo_str)
    for key in kwargs:
        vo[key] = kwargs[key]

    return vo


def authenticate(username, password):
    """
    Authenticate the current profile that is logged in.

    """
    lgn_client = get_lgn_client()

    userVO = _make_VO('vo', 'UserVO')

    userVO.userName = username
    userVO.password = password
    userVO.portalId = 1

    resp = lgn_client.service.authenticate(userVO)
    return resp, lgn_client.options.transport.cookiejar


def change_password(old_password, new_password):
    """
    Change the password given the old password and the new one.
    """
    lgn_client = get_lgn_client()

    passwordVO = _make_VO('vo', 'PasswordVO')

    passwordVO.newPassword = new_password
    passwordVO.oldPassword = old_password

    response = lgn_client.service.changePassword(passwordVO)

    return response


def reset_password(new_password, answer1, answer2, answer3,
                   question1, question2, question3, userName):
    """
    Reset the password given all of the security questions and answers.

    """

    lgn_client = get_lgn_client()

    session = webapp2.get_request().registry.get('session')

    userId = session.get('user_id')

    securityQuestionVO = _make_VO('vo', 'SecurityQuestionVO')

    securityQuestionVO.newPassword = new_password

    securityQuestionVO.reminderAnswer1 = answer1
    securityQuestionVO.reminderQuestion1 = question1

    securityQuestionVO.reminderAnswer2 = answer2
    securityQuestionVO.reminderQuestion2 = question2

    securityQuestionVO.reminderAnswer3 = answer3
    securityQuestionVO.reminderQuestion3 = question3

    securityQuestionVO.userId = userId
    securityQuestionVO.userName = userName

    response = lgn_client.service.resetPassword(securityQuestionVO)

    return response


def create_security_question(answer1, answer2, answer3,
                             question1, question2, question3, userName):
    """
    Create a new security question.

    """

    lgn_client = get_lgn_client()

    session = webapp2.get_request().registry.get('session')

    userId = session.get('user_id')

    securityQuestionVO = _make_VO('vo', 'SecurityQuestionVO')

    securityQuestionVO.reminderAnswer1 = answer1
    securityQuestionVO.reminderQuestion1 = question1

    securityQuestionVO.reminderAnswer2 = answer2
    securityQuestionVO.reminderQuestion2 = question2

    securityQuestionVO.reminderAnswer3 = answer3
    securityQuestionVO.reminderQuestion3 = question3

    securityQuestionVO.userId = userId
    securityQuestionVO.userName = userName

    response = lgn_client.service.createSecurityQuestion(securityQuestionVO)

    return response


def validate_security_question(answer1, answer2, answer3,
                               question1, question2, question3, userName):
    """
    Create a new security question.

    """

    lgn_client = get_lgn_client()

    securityQuestionVO = _make_VO('vo', 'SecurityQuestionVO')

    securityQuestionVO.answer1 = answer1
    securityQuestionVO.question1 = question1

    securityQuestionVO.answer2 = answer2
    securityQuestionVO.question2 = question2

    securityQuestionVO.answer3 = answer3
    securityQuestionVO.question3 = question3

    securityQuestionVO.userName = userName

    response = lgn_client.service.validateSecurityQuestion(securityQuestionVO)

    return response


def get_security_questions(userName):
    """
    Get the current security questions for a user

    """

    lgn_client = get_lgn_client()

    response = lgn_client.service.findSecurityQuestionByUserName(userName)

    return response
