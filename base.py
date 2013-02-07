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
import suds

import logging
import json
import os

from webapp2_extras import sessions
from functools import wraps

log = logging.getLogger(__name__)

version_string = (os.environ['MAJOR_VERSION'] + '.' +
                  os.environ['MINOR_VERSION'])
log.info(version_string)

authentication_failed = "Server raised fault: 'User Credentials Invalid.'"
access_denied = "Server raised fault: 'Access is denied'"


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        log.debug('starting dispatch')
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)
        self.request.registry['session'] = self.session

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        except suds.WebFault as e:
            if e.message == authentication_failed:
                self.response.write(json.dumps({'logged_in': False}))
                self.response.status = 401
            elif e.message == access_denied:
                self.response.write(json.dumps({'logged_in': True,
                                                'message': "Access Denied"}))
                self.response.status = 403
            else:
                self.response.write(json.dumps({
                    'logged_in': True,
                    'message': 'WebFault: {}. See logs'.format(e.message)}))
                self.response.status = 500
                log.exception('Got an unhandled WebFault. Sent a 500 message.')
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
            log.debug('ending dispatch')

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend='datastore')


def login_required(json_=False):
    def decorator(handler_method):
        @wraps(handler_method)
        def check_login(self, *args, **kwargs):
            jsessionid = self.request.registry['session'].get('JSESSIONID')
            if jsessionid is None:
                if json_:
                    self.response.write(json.dumps({'logged_in': False}))
                    self.response.status = 401
                else:
                    self.redirect('/')
            else:
                return handler_method(self, *args, **kwargs)

        return check_login
    return decorator
