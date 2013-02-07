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
# Internal functions which implement asset-y functionality


def get_detailed_assets():
    '''
    Retrieves detailed information about a given asset.

    Returns a dictionary possibly containing but not limited to:
        -Asset's last location
        *The general area of the asset (s.a. "Near Edina, MN")
        *Whether an asset has a >Geofence
                                >Speed Limit
                                >Rash Driving limitations
        -Asset's type, ID#
        -Information about the device

    '''

    response = fms_client.search_asset()

    assets_list = []

    for asset in response.assetVOs:
        a_dict = {'assetId': asset.assetId,
                  'Name': asset.name,
                  'Description': asset.description,
                  'ID_Number': asset.identificationNumber,
                  'Last_Updated': asset.lastUpdated,
                  'Org_ID': asset.organizationId,
                  'status': asset.status,
                  'device_serial': asset.deviceSerial,
                  }
        if asset.assetLastLocationVO is not None:
            a_dict['Last Location'] = {
                'Coordinates': (asset.assetLastLocationVO.latitude,
                                asset.assetLastLocationVO.longitude),
                'Near': asset.assetLastLocationVO.lastLocation,
                'Updated': asset.assetLastLocationVO.locationUpdate,
            }
        else:
            a_dict['Last Location'] = {'Coordinates': (None, None),
                                       'Near': None,
                                       'Updated': None
                                       }

        assets_list.append(a_dict)

    return assets_list


def create_asset(asset_data):
    '''
    Creates a new asset.

    '''

    name = asset_data['name']
    description = asset_data['description']
    deviceID = asset_data['deviceID']
    assetTypeID = asset_data['assetTypeID']

    try:
        status = int(asset_data['status'])
    except ValueError:
        status = 1

    response = fms_client.create_asset(name, description,
                                       deviceID, assetTypeID, status)
    return {'code': response.code,
            'message': response.message,
            }


def modify_asset(asset_id, asset_data):

    '''
    Modifies the asset with ID asset_id to match the parameters
    stored in the asset_data dictionary.

    '''

    name = asset_data['name']
    description = asset_data['description']

    try:
        status = int(asset_data['status'])
    except ValueError:
        status = 1

    try:
        deviceID = asset_data['deviceID']
    except KeyError:
        deviceID = None
    try:
        assetTypeID = asset_data['assetTypeID']
    except KeyError:
        assetTypeID = None

    response = fms_client.modify_asset(asset_id, name, description,
                                       deviceID, assetTypeID, status)
    return response


def delete_asset(asset_id):
    '''
    Deletes the asset with ID number asset_id.

    '''

    response = fms_client.delete_asset(asset_id)
    return response


def get_unused_device_serials(org_id):

    '''
    The aim of this function is to find the serials of all currently
    unused devices.

    To do this, we first retrieve a list of all devices and place
    their serials into a set.

    We then retrieve the list of all assets, extract their associated
    devices' serial numbers and place them into a second set.

    We then obtain the desired result by subtrating the second set from
    the first.

    '''

    devices = device_client.get_devices(org_id)
    assets = fms_client.search_asset()

    all_serials = set()
    taken_serials = set()

    for asset in assets.assetVOs:
        taken_serials.add(asset.deviceSerial)

    for device in devices.deviceVOs:
        all_serials.add(device.serial)

    untaken_serials = all_serials - taken_serials

    return sorted(list(untaken_serials))


def get_asset_types():
    '''
    Get a dictionary of the asset type id's to asset type name.

    '''
    response = fms_client.search_asset_types()
    if not response.assetTypeVOs:
        return {}
    else:
        return {type_.assetTypeId: type_.name
                for type_ in response.assetTypeVOs}


def poll_asset(asset_id):
    '''
    Receive a quick message about the state of the asset.

    '''
    response = fms_client.poll_asset(asset_id)
    return {'code': response.code,
            'message': response.message,
            }


def start_tracking(asset_id):
    '''
    Tell the device to begin sending tracking messages

    '''
    response = fms_client.start_tracking(asset_id)
    return {'code': response.code,
            'message': response.message,
            }


def stop_tracking(asset_id):
    '''
    Tell the device to stop sending tracking messages

    '''
    response = fms_client.stop_tracking(asset_id)
    return {'code': response.code,
            'message': response.message,
            }


#####
# Web services handlers

class AssetHandler(BaseHandler):
    @login_required()
    def assetPage(self):
        self.response.out.write(
            template.render(
                os.path.join('template', 'asset_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def getAllAssets(self):
        self.response.out.write(
            json.dumps({'logged_in': True, 'payload': get_detailed_assets()})
        )

    @login_required(json_=True)
    def createAsset(self):
        asset_data = {}

        try:
            asset_data['name'] = self.request.get('name')
            asset_data['description'] = self.request.get('description')
            asset_data['deviceID'] = self.request.get('deviceID')
            asset_data['assetTypeID'] = self.request.get('assetTypeID')
            asset_data['status'] = self.request.get('status')
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Asset creation failed'}))
            self.response.status = 500
            return
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'message': create_asset(asset_data)})
        )

    @login_required(json_=True)
    def modifyAsset(self, asset_id):
        asset_data = {}
        try:
            asset_data['name'] = self.request.get('name')
            asset_data['description'] = self.request.get('description')
            asset_data['status'] = self.request.get('status')
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Missing parameter "asset_data"'}))
            self.response.status = 500
            return
        try:
            self.response.out.write(
                json.dumps(str(modify_asset(asset_id, asset_data))))
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Asset does not exist'}))
            self.response.status = 404

    @login_required(json_=True)
    def deleteAsset(self, asset_id):
        try:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': str(delete_asset(asset_id))}))
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Asset does not exist'}))
            self.response.status = 404

    @login_required(json_=True)
    def getUnusedDeviceSerials(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_unused_device_serials(org_id)}))

    @login_required(json_=True)
    def getAssetTypes(self):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_asset_types()}))

    @login_required(json_=True)
    def pollAsset(self, asset_id):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': poll_asset(asset_id)}))

    @login_required(json_=True)
    def startTracking(self, asset_id):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': start_tracking(asset_id)}))

    @login_required(json_=True)
    def stopTracking(self, asset_id):
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': stop_tracking(asset_id)}))


# Exported routes
asset_routes = [
    webapp2.Route(r'/', AssetHandler, handler_method='assetPage',
                  methods=['GET']),
    webapp2.Route(r'/asset', AssetHandler, handler_method='getAllAssets',
                  methods=['GET']),
    webapp2.Route(r'/asset', AssetHandler, handler_method='createAsset',
                  methods=['POST']),
    webapp2.Route(r'/asset/<asset_id>', AssetHandler,
                  handler_method='deleteAsset', methods=['DELETE']),
    webapp2.Route(r'/asset/<asset_id>', AssetHandler,
                  handler_method='modifyAsset', methods=['PUT']),
    webapp2.Route(r'/asset/asset_types/', AssetHandler,
                  handler_method='getAssetTypes', methods=['GET']),
    webapp2.Route(r'/device/unused_serial', AssetHandler,
                  handler_method='getUnusedDeviceSerials',
                  methods=['GET']),
    webapp2.Route(r'/poll/<asset_id>', AssetHandler,
                  handler_method='pollAsset', methods=['POST']),
    webapp2.Route(r'/track/<asset_id>', AssetHandler,
                  handler_method='startTracking', methods=['POST']),
    webapp2.Route(r'/stop_track/<asset_id>', AssetHandler,
                  handler_method='stopTracking', methods=['POST']),
]
