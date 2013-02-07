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

import fms_client
from base import version_string, BaseHandler, login_required

#####
# Internal functions for the alerts page

bad_record_types = [10, 19, 20, 21, 30, 31, 53, 65, 67, 69, 70, 92, 93, 95]


def get_single_asset_info(asset_id, bad_record_types):
    '''
    Compiles the alerts and tracks for a specific asset.

    If the asset has any alerts which have a record type in
    bad_record_types, the asset is flagged as trouble=True

    '''
    tracks_resp = fms_client.get_asset_tracks(asset_id).assetTrackVOs
    alerts_resp = fms_client.get_asset_alerts(asset_id).assetAlertVOs
    tracks_resp.extend(alerts_resp)
    records = tracks_resp

    undecorated = [{'Alert': assetRecord.alert,
                    'desc': assetRecord.description,
                    'type': assetRecord.recordType,
                    'distance': assetRecord.cummulativeDistance,
                    'time': assetRecord.dtUpdated,
                    'trouble': (assetRecord.recordType in bad_record_types),
                    'latitude': assetRecord.latitude,
                    'longitude': assetRecord.longitude,
                    }
                   for assetRecord in records]

    decorated = [(r['time'], r) for r in undecorated]
    decorated.sort(reverse=True)

    tracks = {asset_id: [record for (time, record) in decorated]}
    return tracks


class alertHandler(BaseHandler):
    @login_required(json_=True)
    def invalidAlertPage(self):
        self.response.out.write(
            template.render(
                os.path.join('template', 'invalid_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def alertPage(self, asset_id):
        self.response.out.write(
            template.render(
                os.path.join('template', 'alert_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def get_alerts(self, asset_id):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_single_asset_info(
                        asset_id, bad_record_types)}))

alert_routes = [
    webapp2.Route(r'/', alertHandler, handler_method='invalidAlertPage',
                  methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/', alertHandler,
                  handler_method='alertPage', methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/alert/', alertHandler,
                  handler_method='get_alerts', methods=['GET']),
]
