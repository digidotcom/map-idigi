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

from datetime import datetime
from google.appengine.ext.webapp import template
import hashlib
import logging
import json
import os
from socket import error as socket_error
from urllib2 import URLError
import webapp2
from webapp2_extras import routes

from applications.geofence import geofence_routes
from applications.asset import asset_routes
from applications.account import account_routes
from applications.user import user_routes
from applications.obd import obd_routes
from applications.alert import alert_routes
from applications.config import config_routes
from applications.device import device_routes
from applications.org import org_routes

import lgn_client
from base import version_string, BaseHandler, login_required
import keys
import suds

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': keys.session_key,
}

authentication_failed = "Server raised fault: 'User credentials are invalid.'"

log = logging.getLogger(__name__)


class MainHandler(BaseHandler):
    def main_entry(self):
        # see if we already have a valid cookie for a set of credentials
        if self.session.get('JSESSIONID') is None:
            self.response.write(
                template.render(
                    os.path.join('template', 'login.html'),
                    {'version': version_string}))
        else:
            self.response.out.write(
                template.render(
                    os.path.join('template', 'home.html'),
                    {'username': self.session.get('username'),
                     'version': version_string}))

    def login(self):
        username = self.request.get('username')
        password = self.request.get('password')

        try:
            response, cookiejar = lgn_client.authenticate(username, password)
        except (suds.WebFault, socket_error, URLError) as e:
            self.response.out.write(
                template.render(
                    os.path.join('template', 'login.html'),
                    {'error': 'Error communicating with MAP',
                     'version': version_string}))
            return
        if int(response.loginResponse.code) == 200:
            userInfo = response.userProfileVO.userInfo
            self.session['organization_id'] = userInfo.organizationId
            self.session['user_id'] = userInfo.userId

            self.session['username'] = username
            self.session['password'] = password

            for cookie in cookiejar:
                if cookie.name == 'JSESSIONID':
                    self.session['JSESSIONID'] = cookie.value
            self.redirect('/')
        else:
            self.response.out.write(
                template.render(
                    os.path.join('template', 'login.html'),
                    {'error': 'Authentication failed',
                     'version': version_string}))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'session=;')
        self.redirect('/')


app = webapp2.WSGIApplication([
    webapp2.Route(r'/', MainHandler, handler_method='main_entry',
                  methods=['GET']),
    webapp2.Route(r'/', MainHandler, handler_method='login',
                  methods=['POST']),
    webapp2.Route(r'/logout', MainHandler, handler_method='logout',
                  methods=['DELETE', 'GET', 'POST', 'PUT']),
    routes.PathPrefixRoute(r'/geofence', geofence_routes),
    routes.PathPrefixRoute(r'/asset', asset_routes),
    routes.PathPrefixRoute(r'/account', account_routes),
    routes.PathPrefixRoute(r'/user', user_routes),
    routes.PathPrefixRoute(r'/obd', obd_routes),
    routes.PathPrefixRoute(r'/alert', alert_routes),
    routes.PathPrefixRoute(r'/config', config_routes),
    routes.PathPrefixRoute(r'/device', device_routes),
    routes.PathPrefixRoute(r'/org', org_routes),
],
debug=True,
config=config)
