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
import device_client

from base import version_string, BaseHandler, login_required

#####
# Functions for implementing the OBD page


def get_diagnostics(org_id, asset_id):
    '''
    Returns a dictionary of the obd data for one asset.

    '''
    asset_response = fms_client.get_asset(asset_id)
    device_serial = asset_response.assetVO.deviceSerial

    response = fms_client.get_diagnostic_data(device_serial)

    if not 'diagnosticDataVOs' in response:
        return

    elif len(response.diagnosticDataVOs) == 0:
        diagnostics = {asset_id: [{
            'Absolute Throttle Position': None,
            'AirIntake Temperature': None,
            'Cruise Control Status': None,
            'Cumulative Fuel Used': None,
            'Date Created': None,
            'Device Serial': device_serial,
            'Diagnostic Data Id': None,
            'Dtc Errors': None,
            'Dtc Value': None,
            'Engine Coolant Temperature': None,
            'Engine Rpm': None,
            'Ignition State': None,
            'Instantaneous Fuel Rate': None,
            'Load Percentage': None,
            'Long Term Fuel Trim': None,
            'Mass Air Flow': None,
            'Odometer Reading': None,
            'Pto Information': None,
            'Record Type': None,
            'Short Term Fuel Trim': None,
            'Speed': None
        }]}
    else:
        # Diagnostics is a data stucture of the form:
        # {asset_id: [{key1: value1, key2: value2, ... }
        #             {key1: value1, key2: value2, ... }
        #             ...
        #            ]
        # }
        diagnostics = {
            asset_id: [
                {make_readable(record[0]): record[1] for record in OBDdata}
                for OBDdata in response.diagnosticDataVOs
            ]
        }

    return diagnostics


def get_all_diagnostics(org_id):
    '''
    Returns the obd data for all assets.

    Note that this function can take a long time to execute, due
    to the fact that each asset requires its own call and response
    from the MAP server. This code is not used in these applications.

    '''
    asset_response = fms_client.search_asset()
    asset_dev_serials = {asset.deviceSerial: asset.assetId
                         for asset in asset_response.assetVOs}

    device_response = device_client.get_devices(org_id)

    # This is slightly backward, but it makes sure that only devices
    # currently connected to assets become part of the response
    asset_dev_ids = {asset_dev_serials[device.serial]: device.deviceId
                     for device in device_response.deviceVOs
                     if device.serial in asset_dev_serials}

    diagnostics = [
        {'asset': asset,
         'obd': fms_client.get_diagnostic_data(
             device_id=asset_dev_ids[asset]).diagnosticDataVOs}
        for asset in asset_dev_ids]

    return diagnostics


def make_readable(string):
    '''
    Takes a string in 'camelCase' and converts it to 'Camel Case'.

    Purely a superficial change to make the web interface cleaner.

    '''
    output = []
    output.append(string[0].upper())
    for char in string[1:]:
        if char.isupper():
            output.append(' ')
        output.append(char)
    return ''.join(output)


class OBDHandler(BaseHandler):
    @login_required(json_=True)
    def obdPage(self):
        self.response.out.write(
            template.render(
                os.path.join('template', 'invalid_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def obdPage(self, asset_id):
        self.response.out.write(
            template.render(
                os.path.join('template', 'obd_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    '''
    @login_required(json_=True)
    def getAllOBDs(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_all_diagnostics(org_id)}))
    '''

    @login_required(json_=True)
    def updateOBD(self, asset_id):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_diagnostics(org_id, asset_id)}))

    '''
    #Forgive me, for I have sinned.
    @login_required(json_=True)
    def getAssets(self):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': [asset.assetId for asset in
                                    fms_client.search_asset().assetVOs]}))
    '''

obd_routes = [
    webapp2.Route(r'/obd/', OBDHandler, handler_method='invalidObdPage',
                  methods=['GET']),
    webapp2.Route(r'/', OBDHandler, handler_method='invalidObdPage',
                  methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/', OBDHandler,
                  handler_method='obdPage', methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/obd/', OBDHandler,
                  handler_method='updateOBD', methods=['GET']),
]
