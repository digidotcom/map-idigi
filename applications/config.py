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
# Internal Data-Handling Functions

def _update_combined(combined, featureVOs):
    '''
    Updates attributes inside a feature without clobbering
    any of the un-updated attributes.

    '''
    for feature in featureVOs:
        key = (feature.featureId, feature.featureName)
        combined.setdefault(key, dict())
        combined[key].update(
            {attr.attrId: attr for attr in feature.attributeVOs})


def create_current_config(org_id, asset_id):
    '''
    Creates a consumable representation of an asset's current configuration.

    Merges the current configuration of a device with the list of
    all possible features to be configured for a device of its type.

    It then transorms this information into a structure useable by
    the templating engine.

    '''
    #Get the asset's configuration and its device type's default configuration
    asset = fms_client.get_asset(asset_id)
    serial = asset.assetVO.deviceSerial
    device = device_client.get_device(org_id, serial=serial)
    type_ = device.deviceVO.deviceTypeVO.deviceTypeId

    deviceResponse = device_client.get_device_configuration(serial)
    defaultResponse = device_client.get_device_type_configuration(type_)

    #Combine the current configuration with the default one
    combined_dict = {}
    _update_combined(
        combined_dict,
        defaultResponse.deviceTypeConfigurationVO.featureVOs)

    if deviceResponse.deviceConfigurationVO is not None:
        # a device's config only exists if it's been configured previously
        _update_combined(
            combined_dict,
            deviceResponse.deviceConfigurationVO.featureVOs)

    #Create a data structure suitable for the template. Note that this
    # is specific to these applications and not especially important
    device_config_list = []
    for feature_id, feature_name in combined_dict:
        feat = {'id': feature_id,
                'name': feature_name,
                'attrs': sorted(combined_dict[(feature_id,
                                               feature_name)].values(),
                                key=lambda attr: attr.attrName)  # sort by name
                }

        device_config_list.append(feat)

    return sorted(device_config_list, key=lambda element: element['name'])


def send_configuration(asset_id, config_data):
    '''
    Overwrites the asset's configuration with the one given on the page.

    The page's form data is parsed and sanitized, then inserted in the
    appropriate places in the default configuration. This function sends
    every feature, but notice that this isn't necessary. If only one option
    is changed, only that feature needs to be sent back to the device.

    '''
    #Get the device type's default configuration
    asset = fms_client.get_asset(asset_id)
    serial = asset.assetVO.deviceSerial
    device = device_client.get_device(asset.assetVO.organizationId,
                                      serial=serial)
    type_ = device.deviceVO.deviceTypeVO.deviceTypeId
    default = device_client.get_device_type_configuration(type_)

    # Set up default configuration details for quick access
    features = default.deviceTypeConfigurationVO.featureVOs
    feat_names = {f.featureId: f.featureName for f in features}
    default_attrs = {feature.featureId: {attribute.attrId: attribute
                                         for attribute in feature.attributeVOs}
                     for feature in features}

    # Set up form data for insertion into default_attrs. Note that this is
    # specific to this application.
    new_configs = {}
    for (feat_attr, attr_value) in config_data:
        # This is where the strange form names come in handy
        feat_id, attr_id = [int(elem) for elem in feat_attr.split('_')]
        new_configs.setdefault(feat_id, {})
        new_configs[feat_id][attr_id] = attr_value

    #Sanitize form data and insert back into the default configurations
    changed_features = []
    for feat_id in new_configs:
        changed_features.append(feat_id)

        for attr_id in new_configs[feat_id]:
            attr_value = new_configs[feat_id][attr_id]
            if attr_value == 'on':
                attr_value = '1'
            if attr_value == '':
                attr_value = None

            default_attrs[feat_id][attr_id].attrValue = attr_value

    #Revert default_configs to a nested list structure
    configuration = []

    for feat_id in changed_features:
        featureVO = device_client.create_feature(feat_id, feat_names[feat_id])
        featureVO.attributeVOs = default_attrs[feat_id].values()
        configuration.append(featureVO)

    #Note that `configuration' is now in the correct data structure for sending
    # to MAP and the device. That is, configuration is a list of features, each
    # of which is a list of attributes. Each attribute has an attrName and an
    # attrValue field, as well as some secretarial fields like min, max, and ID
    response = device_client.update_configuration(serial, configuration)
    return {'code': response.code,
            'message': response.message,
            }


class configHandler(BaseHandler):
    @login_required(json_=True)
    def configPage(self):
        self.response.out.write(
            template.render(
                os.path.join('template', 'invalid_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def getConfig(self, asset_id):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            template.render(
                os.path.join('template', 'config_tmpl.html'),
                {'username': self.session.get('username'),
                 'pageData': create_current_config(org_id, asset_id),
                 'version': version_string}))

    @login_required(json_=True)
    def sendConfig(self, asset_id):
        config_fields = self.request.arguments()
        new_config_data = []
        for entry in config_fields:
            # Explicitly converting from unicode to strings
            new_config_data.append((str(entry), str(self.request.get(entry))))

        self.response.out.write(
            json.dumps({'logged_in': True,
                        'message': send_configuration(asset_id,
                                                      new_config_data)}))

config_routes = [
    webapp2.Route(r'/', configHandler, handler_method='configPage',
                  methods=['GET']),
    webapp2.Route(r'/config/asset/<asset_id>', configHandler,
                  handler_method='getConfig', methods=['GET']),
    webapp2.Route(r'/config/asset/<asset_id>', configHandler,
                  handler_method='sendConfig', methods=['PUT']),
]
