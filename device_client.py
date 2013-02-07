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

import random
from os import environ

import webapp2
from suds.client import Client
from suds.sax.element import Element

wsdl_base = environ['MAP_WSDL_BASE']

DEV_URL = '{}DeviceManagementService?wsdl'.format(wsdl_base)


def get_device_client():
    '''
    Returns a soap client object.

    If an object has already been created, we recyle it,
    otherwise, a new one is created and returned.

    '''
    app = webapp2.get_app()
    request = webapp2.get_request()

    # check if we already have the client
    username = request.registry['session'].get('username')
    password = request.registry['session'].get('password')
    device_key = 'device_client:{}'.format(username)

    # check if we aleady have the client
    device_client = app.registry.get(device_key)
    if not device_client:
        device_client = Client(DEV_URL, cache=None)
        device_client.add_prefix(
            'rsp', "http://response.devicemanagement.core.mtrak.digi.com/xsd")
        device_client.add_prefix(
            'srv', "http://service.devicemanagement.core.mtrak.digi.com")
        device_client.add_prefix(
            'vo', "http://vo.devicemanagement.core.mtrak.digi.com/xsd")

        app.registry[device_key] = device_client

    device_client.set_options(soapheaders=(
        Element('username').setText(username),
        Element('password').setText(password)))

    return device_client


def _make_VO(namespace, name, **kwargs):
    '''
    Creates a Suds SOAP value object.

    namespace = string
    name = string

    '''
    device_client = get_device_client()
    vo_str = namespace + ':' + name
    vo = device_client.factory.create(vo_str)
    for key in kwargs:
        vo[key] = kwargs[key]

    return vo


def get_devices(org_id):
    '''
    Returns a SOAP object containing all devices associated
    with an account.

    '''
    client = get_device_client()
    deviceVO = _make_VO('vo', 'DeviceVO')
    deviceVO.organizationId = org_id

    response = client.service.searchDevice(deviceVO)
    return response


def get_device(org_id, serial=None, dev_id=None):
    '''
    Returns a SOAP object containing all devices associated
    with an account.

    '''
    client = get_device_client()
    deviceVO = _make_VO('vo', 'DeviceVO')
    deviceVO.organizationId = org_id
    deviceVO.serial = serial
    deviceVO.deviceId = dev_id

    response = client.service.getDevice(deviceVO)
    return response


def create_feature(feature_id, feature_name):
    '''
    Returns a featureVO. Note that this function does not
    make a call to the server.

    '''
    client = get_device_client()
    featureVO = _make_VO('vo', 'FeatureVO')
    featureVO.featureId = feature_id
    featureVO.featureName = feature_name

    return featureVO


def get_device_type_configuration(dev_type=None, serial=None):
    '''
    Returns a SOAP object containing the default device type
    configuration

    '''
    client = get_device_client()
    int_id = _make_VO('vo', 'IntIdVO')
    int_id.id = dev_type

    response = client.service.getDeviceTypeConfiguration(int_id)
    return response


def get_device_configuration(dev_serial):
    '''
    Returns a SOAP object containing the current configuration
    for a specific device.

    '''
    client = get_device_client()
    serial = _make_VO('vo', 'DeviceSerialVO')
    serial.serial = dev_serial

    response = client.service.getDeviceConfiguration(serial)
    return response


def update_configuration(serial, configuration):
    '''
    Sends a pre-fabricated configuration to an asset

    '''
    client = get_device_client()
    deviceConfigVO = _make_VO('vo', 'DeviceConfigurationVO')
    deviceConfigVO.featureVOs = configuration
    deviceConfigVO.serial = serial

    response = client.service.updateDeviceConfiguration(deviceConfigVO)
    return response


def provision_device(deviceType, mobileOperator, mobileNumber, organizationId,
                     macAddress=None, IMEI=None, serial=None):
    '''
    Provisions a device in the mCore service.

    This action will also add the device to iDigi.
    '''
    client = get_device_client()
    provDeviceVO = _make_VO('vo', 'ProvisionDeviceVO')

    provDeviceVO.deviceType = deviceType
    provDeviceVO.mobileOperator = mobileOperator
    provDeviceVO.mobileNumber = mobileNumber
    provDeviceVO.organizationId = organizationId

    # These settings are individually optional (but one is required)
    provDeviceVO.macAddress = macAddress
    provDeviceVO.IMEI = IMEI
    provDeviceVO.serial = serial

    response = client.service.provisionDevice(provDeviceVO)
    return response


def list_mobile_operators():
    '''List the mobile operators available on mCore.'''

    client = get_device_client()
    response = client.service.listMobileOperators()
    return response


def search_device_types(status=1):
    '''Find device types with *status*.'''
    client = get_device_client()
    # I don't actually know what the status means, but every device type is
    # status 0. - Mathew Ryden

    typeVO = _make_VO('vo', 'DeviceTypeVO')

    typeVO.status = status

    response = client.service.searchDeviceType(typeVO)
    return response
