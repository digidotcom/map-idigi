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
import logging
import os
import re
import random

import fms_client
from base import version_string, BaseHandler, login_required
try:
    import keys
except ImportError as ie:
    raise ImportError(
        "Unable to import keys. This file is generated from "
        "keys_temp.py. See documentation.")


log = logging.getLogger(__name__)

#####
# Internal functions which implement geofencing functionality


def get_assets():
    """
    Get assets associated with the account.

    Returns a dictionary of with keys name, description of all
    assets associated with an account.

    """
    response = fms_client.search_asset()

    return {asset.assetId: {'name': asset.name,
                            'description': asset.description}
            for asset in response.assetVOs}


def get_last_location(asset_id):
    """
    Get the last location for an asset.

    Returns a dict of lat/long and the last time updated.
    If the asset has no last location, returns None.
    If the asset doesn't exist on the account, raises KeyError.

    """
    response = fms_client.get_asset(asset_id=asset_id)

    if response.assetVO is None:
        raise KeyError("Asset Does Not Exist!")

    asset = response.assetVO
    if asset.assetLastLocationVO is None:
        return None
    else:
        last_location = asset.assetLastLocationVO
        return {'latitude': last_location.latitude,
                'longitude': last_location.longitude,
                'updated': last_location.dtUpdated}


def get_geofence(asset_id):
    """Get the currently set geofence for an asset.

    Will return one of the geofences if multiple are set.

    Returns a list of [latitude, longitude] for the set geofence, if set.
    Returns None if no geofence is set
    Raises KeyError if the asset does not exist.

    """
    response = fms_client.get_asset(asset_id=asset_id)

    if response.assetVO is None:
        raise KeyError("Asset Does Not Exist!")

    if 'geofenceVOs' not in response.assetVO:
        # no geofence is set
        return None

    # Note that without str() points_string would be a suds 'Text' object
    points_string = str(response.assetVO.geofenceVOs[0].geofenceGeometry)

    # from http://bit.ly/KOB9JI (stackoverflow comment)
    # Match all numbers in the POLYGON((long lat,long lat, ...., long lat))
    # string
    nums = map(float, re.findall(
        r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
        points_string))
        # Assume valid format

    parsed = [(latitude, longitude) for longitude, latitude in
              zip(nums[::2], nums[1::2])]

    if not parsed:
        return None
    else:
        return parsed


def set_geofence(asset_id, geofence, inclusivity):
    """
    Set a geofence for an asset.

    First, removes all current geofences attached to the asset.
    (This is not necessary, but this app limits assets to only one
    fence for simplicity's sake.)

    Then the geofence passed as a parameter is applied to the asset.
    If the geofence is empty, clears the existing geofence.

    A random type name is associated with each fence to show
    functionality.

    Raises RuntimeError we get an error or unexpected data from mCore.
    Raises KeyError if the asset does not exist.

    """
    geofence = [(float(x), float(y)) for x, y in list(geofence)]

    a_response = fms_client.get_asset(asset_id=asset_id)
    if 'assetVO' not in a_response:
        raise KeyError('Asset does not exist')

    if 'geofenceVOs' in a_response.assetVO:
        for fence in a_response.assetVO.geofenceVOs:
            fms_client.delete_geofence(fence.geofenceId)

    if not geofence:
        # No geofence to add. Done
        return

    geo_id = {'inclusive': 1,
              'exclusive': 2,
              }
    geofence_type = str(random.randint(0, 100))

    request = webapp2.get_request()
    org_id = request.registry['session'].get('organization_id')
    fms_client.create_geofenceType(1, geofence_type)
    g_response = fms_client.create_geofence(geofence,
                                            "asset" + str(asset_id) + "_fence",
                                            geo_id[inclusivity],
                                            geofence_type,
                                            org_id)
    log.info(g_response)

    if 'entityId' in g_response:
        resp = fms_client.apply_geofence(asset_id, g_response.entityId)
        return {'code': resp.code,
                'message': resp.message}
    else:
        raise RuntimeError(str(g_response))


#####
# Web services handlers


class GeofenceHandler(BaseHandler):
    @login_required()
    def geofencePage(self):
        """Get geofence html."""
        self.response.out.write(
            template.render(
                os.path.join('template', 'geofence_tmpl.html'),
                {'username': self.session.get('username'),
                 'maps_key': keys.google_maps_key,
                 'version': version_string}))

    @login_required(json_=True)
    def getAssets(self):
        """Get all the assets associated with an account."""
        self.response.out.write(json.dumps({'logged_in': True,
                                            'payload': get_assets()}))

    @login_required(json_=True)
    def getLastLocation(self, asset_id):
        """Get the last location of an asset."""
        try:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'payload': get_last_location(asset_id)}))
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Asset does not exist.'}))
            self.response.status = 404

    @login_required(json_=True)
    def getGeofence(self, asset_id):
        """Get and set geofences for a specific asset."""
        try:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'payload': get_geofence(asset_id)}))
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Asset does not exist.'}))
            self.response.status = 404

    @login_required(json_=True)
    def setGeofence(self, asset_id):
        try:
            geofence = self.request.get('fence')
            inclusivity = self.request.get('id')
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Missing parameter "fence".'}))
            self.response.status = 500
            return
        geofence = json.loads(geofence)
        log.info(geofence)

        try:
            resp = set_geofence(asset_id, geofence, inclusivity)
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Asset does not exist.'}))
            self.response.status = 404
        except RuntimeError, e:
            self.response.out.write(json.dumps({'logged_in': True,
                                                'message': str(e)}))
            self.response.status = 400

        resp['logged_in'] = True
        self.response.out.write(
            json.dumps(resp))


# Exported routes
geofence_routes = [
    webapp2.Route(r'/', GeofenceHandler, handler_method='geofencePage',
                  methods=['GET']),
    webapp2.Route(r'/asset', GeofenceHandler, handler_method='getAssets',
                  methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/location', GeofenceHandler,
                  handler_method='getLastLocation', methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/geofence', GeofenceHandler,
                  handler_method='getGeofence', methods=['GET']),
    webapp2.Route(r'/asset/<asset_id>/geofence', GeofenceHandler,
                  handler_method='setGeofence', methods=['PUT']),
]
