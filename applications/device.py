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

import device_client
from base import version_string, BaseHandler, login_required


def provision_device(device_data):
    mobile_number = device_data['mobile_number']
    mobile_operator = device_data['mobile_operator']
    IMEI = device_data['IMEI']
    mac_address = device_data['mac_address']
    org_id = device_data['org_id']
    device_type = device_data['device_type']
    serial = device_data['serial']

    if not IMEI:
        IMEI = ''
    if not mac_address:
        mac_address = ''
    if not serial:
        serial = ''

    return device_client.provision_device(device_type,
                                          mobile_operator, mobile_number,
                                          org_id, macAddress=mac_address,
                                          IMEI=IMEI, serial=serial)


def mobile_operators():
    response = device_client.list_mobile_operators()
    if not response.mobileOperatorVOs:
        return
    else:
        return {operator.operatorId: operator.name
                for operator in response.mobileOperatorVOs}


def device_types():
    response = device_client.search_device_types()

    if not response.deviceTypeVOs:
        return
    return {type.deviceTypeId: type.name for type in response.deviceTypeVOs}


class deviceHandler(BaseHandler):
    @login_required(json_=True)
    def devicePage(self, *args):
        self.response.out.write(
            template.render(
                os.path.join('template', 'device_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def postProvision(self):
        device_data = {}
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')

        try:
            device_data['mobile_number'] = self.request.get('mobile_number')
            device_data['mobile_operator'] = self.request.get(
                'mobile_operator')
            device_data['IMEI'] = self.request.get('IMEI')
            device_data['mac_address'] = self.request.get('mac_address')
            device_data['org_id'] = org_id
            device_data['device_type'] = self.request.get('device_type')
            device_data['serial'] = self.request.get('serial')
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Device Provisioning failed'}))
            self.response.status = 500
            return

        response = provision_device(device_data)
        if response.entityId is None:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': response.message}))
            self.response.status = 502
            return
        else:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': response.message,
                            'code': response.code}))

    @login_required(json_=True)
    def get_device_types(self):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': device_types()}))

    @login_required(json_=True)
    def get_operators(self):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': mobile_operators()}))


device_routes = [
    webapp2.Route(r'/', deviceHandler, handler_method='devicePage',
                  methods=['GET']),
    webapp2.Route(r'/device/', deviceHandler, handler_method='postProvision',
                  methods=['PUT']),
    webapp2.Route(r'/device/device_types/', deviceHandler,
                  handler_method='get_device_types', methods=['GET']),
    webapp2.Route(r'/device/mobile_operators/', deviceHandler,
                  handler_method='get_operators', methods=['GET']),
]
