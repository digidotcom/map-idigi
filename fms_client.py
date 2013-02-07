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

import copy
import datetime as dt
import logging
from os import environ
import uuid

import webapp2
from suds.client import Client
from suds.sax.element import Element

wsdl_base = environ['MAP_WSDL_BASE']

log = logging.getLogger(__name__)

FMS_URL = '{}FleetManagementService?wsdl'.format(wsdl_base)


def get_fms_client():
    '''
    Returns a soap client object.

    If an object has already been created, we recyle it,
    otherwise, a new one is created and returned.

    '''
    app = webapp2.get_app()
    request = webapp2.get_request()

    username = request.registry['session'].get('username')
    password = request.registry['session'].get('password')
    fms_key = 'fms_client:{}'.format(username)

    # check if we already have the client
    fms_client = app.registry.get(fms_key)
    if not fms_client:
        fms_client = Client(FMS_URL, cache=None)
        fms_client.add_prefix(
            'rsp', "http://response.atms.core.mtrak.digi.com/xsd")
        fms_client.add_prefix(
            'srv', "http://service.atms.core.mtrak.digi.com")
        fms_client.add_prefix(
            'vo', "http://vo.atms.core.mtrak.digi.com/xsd")

        app.registry[fms_key] = fms_client

    fms_client.set_options(soapheaders=(
        Element('username').setText(username),
        Element('password').setText(password)))

    return fms_client


def _make_VO(namespace, name, **kwargs):
    '''
    Creates a Suds SOAP value object.

    namespace = string
    name = string

    Note that the function does not check to see that any of the
    keyword arguments are valid, and that any invalid mappings will
    be added to the VO.
    '''
    fms_client = get_fms_client()
    vo_str = namespace + ':' + name
    vo = fms_client.factory.create(vo_str)
    for key in kwargs:
        vo[key] = kwargs[key]

    return vo


def create_geofence(points, name, gf_id, gf_type, org_id):
    '''
    Creates a new geofence in iDigiMA using the given points.

    Additionally, it makes sure that a polygon for a given geofence
    is valid before the SOAP call is sent to prevent needless errors.

    '''
    fms_client = get_fms_client()
    geofenceVO = _make_VO('vo', 'GeofenceVO')

    if (points is None) or (len(points) < 3):
        raise RuntimeError("Geofence needs at least 3 points")

    #Ensures the fence's first and last points are equal
    if points[0] != points[len(points) - 1]:
        points = points + [points[0]]

    poly = 'POLYGON(({pts}))'.format(pts=','.join('{y} {x}'.format(x=x, y=y)
                                                  for x, y in points))
    geofenceVO.geofenceGeometry = poly
    geofenceVO.geofenceName = name
    geofenceVO.geofenceId = gf_id
    geofenceVO.geofenceType = gf_type
    geofenceVO.organizationId = org_id

    response = fms_client.service.createGeofence(geofenceVO)
    return response


def delete_geofence(gf_id):
    '''
    Deletes a specific geofence from iDigiMA

    '''
    fms_client = get_fms_client()
    response = fms_client.service.deleteGeofence(gf_id)

    return response


def create_geofenceType(gft_id, name):
    '''
    Creates a new geofence type in iDigiMA.

    All geofences need to be associated with a type, which we have
    hardcoded for simplicity

    '''
    fms_client = get_fms_client()
    typeVO = _make_VO('vo', 'GeofenceTypeVO')
    typeVO.typeId = gft_id
    typeVO.typeName = name

    response = fms_client.service.createGeofenceType(typeVO)
    return response


def apply_geofence(asset_id, gf_id):
    '''
    Applies an existing geofence to an existing asset.

    '''
    fms_client = get_fms_client()
    assetGeofenceVO = _make_VO('vo', 'AssetGeofenceVO')

    assetGeofenceVO.assetId = asset_id
    assetGeofenceVO.geofenceIds = [gf_id]

    response = fms_client.service.applyGeofence(assetGeofenceVO)
    return response


def search_asset():
    '''
    Returns a SOAP object containing all assets tied to the given account

    '''
    fms_client = get_fms_client()
    assetVO = _make_VO('vo', 'SearchAssetVO')
    assetVO.fromLimit = 0
    assetVO.toLimit = 1000000

    response = fms_client.service.searchAsset(assetVO)
    return response


def search_asset_types(status=1):
    '''
    Returns a SOAP object containing all asset types with *status*

    '''
    fms_client = get_fms_client()
    assetTypeVO = _make_VO('vo', 'AssetTypeVO')
    assetTypeVO.status = status

    response = fms_client.service.searchAssetType(assetTypeVO)
    return response


def get_asset(asset_id):
    '''
    Returns a SOAP object containing information about a specific asset

    '''
    fms_client = get_fms_client()
    assetIdVO = _make_VO('vo', 'AssetIdVO')

    assetIdVO.assetId = asset_id

    response = fms_client.service.getAsset(assetIdVO)
    return response


def delete_asset(asset_id):
    '''
    Deletes an asset from the mCore database.

    This entails decoupling the asset from its respective device.
    However, the device still exists both in iDigi and in mCore.

    '''
    fms_client = get_fms_client()
    assetIdVO = _make_VO('vo', 'AssetIdVO')

    assetIdVO.assetId = asset_id

    response = fms_client.service.deleteAsset(assetIdVO)
    return response


def modify_asset(asset_id, name, description, dev_serial, assetTypeID, status):
    '''
    Modify the asset with ID asset_id to match the parameters name,
    description, assetTypeID, deviceSerial and status.

    '''
    fms_client = get_fms_client()
    assetVO = get_asset(asset_id).assetVO

    if assetTypeID is not None:
        assetTypeVO = _make_VO('vo', 'AssetTypeVO')
        assetTypeVO.assetTypeId = assetTypeID
        sa_response = fms_client.service.searchAssetType(assetTypeVO)
        if len(sa_response.assetTypeVOs):
            assetVO.assetTypeVO = sa_response.assetTypeVOs[0]
        else:
            assetVO.assetTypeVO = assetTypeVO

    if dev_serial is not None:
        assetVO.deviceSerial = dev_serial

    if status in [1, 2, 3, 4, 5]:
        pass
    else:
        status = 1

    assetVO.description = description
    assetVO.status = status
    assetVO.name = name
    response = fms_client.service.updateAsset(assetVO)
    return response


def create_asset(name, description, deviceID, assetTypeID, status):
    '''
    Create a new asset with provided name, description, deviceID,
    assetTypeID, and status.

    '''
    fms_client = get_fms_client()

    assetTypeVO = _make_VO('vo', 'AssetTypeVO')
    assetTypeVO.assetTypeId = assetTypeID

    searchAssetTypeResponse = fms_client.service.searchAssetType(assetTypeVO)

    assetVO = _make_VO('vo', 'AssetVO')

    if len(searchAssetTypeResponse.assetTypeVOs):
        assetVO.assetTypeVO = searchAssetTypeResponse.assetTypeVOs[0]
    else:
        assetVO.assetTypeVO = assetTypeVO

    if status in [1, 2, 3, 4, 5]:
        pass
    else:
        status = 1

    assetVO.name = name
    assetVO.deviceSerial = deviceID
    assetVO.description = description
    assetVO.status = status
    assetVO.identificationNumber = str(uuid.uuid4())
    assetVO.installationDate = make_time_string(dt.datetime.utcnow())
    response = fms_client.service.createAsset(assetVO)
    return response


def get_diagnostic_data(device_serial):
    '''
    Returns a SOAP response containing the onboard diagnistic data
    for the asset.

    Call with a device serial (as found in a response from get_asset()

    '''
    fms_client = get_fms_client()

    deviceIdVO = _make_VO('vo', 'DeviceIdVO')
    deviceIdVO.deviceId = device_serial
    diag_response = fms_client.service.getDiagnosticData(deviceIdVO)

    return diag_response


def get_asset_tracks(asset_id):
    '''
    Returns the bare SOAP response containing an asset's track data

    '''
    fms_client = get_fms_client()

    FMSInputVO = _make_VO('vo', 'FMSInputVO')
    FMSInputVO.assetId = asset_id

    # For the sake of this sample app,
    #  just show the last 100 alerts from the last year
    FMSInputVO.fromLimit = 0
    FMSInputVO.toLimit = 100
    FMSInputVO.toTime = make_time_string(dt.datetime.utcnow())
    FMSInputVO.fromTime = make_time_string(dt.datetime.utcnow() -
                                           dt.timedelta(days=365))

    response = fms_client.service.getAssetTracksByAssetID(FMSInputVO)
    return response


def get_asset_alerts(asset_id):
    '''
    Returns the bare SOAP response containing an asset's track data

    This is very similar to get_asset_tracks, the only difference being
    that some messages from the device are categorized as 'tracks'
    (such as position data) and others as 'alerts' (such as rash driving).

    '''
    fms_client = get_fms_client()

    FMSInputVO = _make_VO('vo', 'FMSInputVO')
    FMSInputVO.assetId = asset_id

    # For the sake of this sample app,
    #  just show the last 100 alerts from the last year
    FMSInputVO.fromLimit = 0
    FMSInputVO.toLimit = 100
    FMSInputVO.toTime = make_time_string(dt.datetime.utcnow())
    FMSInputVO.fromTime = make_time_string(dt.datetime.utcnow() -
                                           dt.timedelta(days=365))

    response = fms_client.service.getAssetAlertsByAssetID(FMSInputVO)
    return response


def poll_asset(asset_id):
    '''
    Recieve a quick message from the asset.

    '''
    fms_client = get_fms_client()

    assetIdVO = _make_VO('vo', 'AssetIdVO')
    assetIdVO.assetId = asset_id

    response = fms_client.service.pollAsset(assetIdVO)
    return response


def start_tracking(asset_id):
    '''
    Tell the asset to begin sending tracking messages.

    '''
    fms_client = get_fms_client()

    assetIdVO = _make_VO('vo', 'AssetIdVO')
    assetIdVO.assetId = asset_id

    response = fms_client.service.startTracking(assetIdVO)
    return response


def stop_tracking(asset_id):
    '''
    Tell the asset to begin sending tracking messages.

    '''
    fms_client = get_fms_client()

    assetIdVO = _make_VO('vo', 'AssetIdVO')
    assetIdVO.assetId = asset_id

    response = fms_client.service.stopTracking(assetIdVO)
    return response


def make_time_string(t):
    '''
    Returns a correctly formatted timestamp given a datetime object.

    For compatibility reasons it rounds to the nearest second.

    '''
    return t.strftime('%Y-%m-%d %H:%M:%S.000')


def make_time_from_string(string):
    '''
    Takes the time format used in the MAP server
    and returns a datetime object.

    '''
    return dt.datetime.strptime(string, '%Y-%m-%d %H:%M:%S.%f')
