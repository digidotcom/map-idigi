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

import datetime
from os import environ
import uuid

import webapp2
from suds.client import Client
from suds.sax.element import Element

wsdl_base = environ['MAP_WSDL_BASE']

NOTIF_URL = '{}NotificationService?wsdl'.format(wsdl_base)


def get_notif_client():
    '''
    Returns a soap client object.

    If an object has already been created, we recyle it,
    otherwise, a new one is created and returned.

    '''
    app = webapp2.get_app()
    request = webapp2.get_request()

    username = request.registry['session'].get('username')
    password = request.registry['session'].get('password')
    notif_key = 'notif_client:{}'.format(username)

    # check if we already have the client
    notif_client = app.registry.get(notif_key)
    if not notif_client:
        notif_client = Client(NOTIF_URL, cache=None)
        notif_client.add_prefix(
            'rsp', "http://response.atms.core.mtrak.digi.com/xsd")
        notif_client.add_prefix(
            'srv', "http://service.atms.core.mtrak.digi.com")
        notif_client.add_prefix(
            'vo', "http://vo.atms.core.mtrak.digi.com/xsd")

        app.registry[notif_key] = notif_client

    notif_client.set_options(soapheaders=(
        Element('username').setText(username),
        Element('password').setText(password)))

    return notif_client


def _make_VO(namespace, name, **kwargs):
    '''
    Creates a Suds SOAP value object.

    namespace = string
    name = string

    '''
    notif_client = get_notif_client()
    vo_str = namespace + ':' + name
    vo = notif_client.factory.create(vo_str)
    for key in kwargs:
        vo[key] = kwargs[key]

    return vo


def create_recipient_group(org_id):
    pass
