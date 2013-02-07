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
import json
import logging
import os
import traceback
import webapp2

import user_client
from base import version_string, BaseHandler, login_required

log = logging.getLogger(__name__)

#####
# Internal functions which implement organization functionality


def possible_parents(org_id):
    '''
    Give org_id's of all orgs the current user has access to

    In practice, this function should return all of the same
    organizations which show up on the /org page, plus the
    organization of the current user.

    '''
    sub_orgs = user_client.search_organization(org_id=org_id,
                                               status=1, type_id=1)
    current_org = get_org(org_id)

    if 'organizations' in sub_orgs.organizationsVO:
        all_possible = [{'id': org.organizationId,
                         'name': org.name,
                         }
                        for org in sub_orgs.organizationsVO.organizations]
    else:
        all_possible = []

    all_possible.insert(0, {'id': current_org['orgId'],
                            'name': current_org['name'],
                            })

    return all_possible


def create_org(org_info):
    '''
    Creates a new sub-organization and creates useful permission categories.

    See user_client.create_organization()
    for more information on organizations, and
    helpers.create_permissions() for more information
    on creating user groups and user permissions.

    '''
    original_status = int(org_info.get('status', 1))  # Default to active
    org_info['status'] = 1  # Set the organization to inactive. Activate later

    response = user_client.create_organization(**org_info)
    new_org_id = response.organizationVO.organizationId

    # Have a template for a long error if we have a problem creating
    # permissions and it fails, and then we fail to deactivate the
    # organization
    org_deletion_failure_templ = (
        'Error creating permissions. Org ({}) deactivation failed. '
        'Organization must be deactivated manually or it will show '
        'up in the organization listing.'
    )

    try:
        user_client.create_permissions(new_org_id)
    except Exception, e:
        try:
            user_client.deActivate_organization(new_org_id)
        except Exception as e:
            return {'code': 500,
                    'message': org_deletion_failure_templ.format(new_org_id),
                    'id': None,
                    }
        else:
            return {'code': 500,
                    'message': traceback.format_exc(e),
                    'id': None,
                    }

    # Activate the organization with proper permissions
    if original_status == 2:
        try:
            user_client.deActivate_organization(new_org_id)
        except Exception as e:
            return {'code': 500,
                    'message': traceback.format_exc(e),
                    'id': None,
                    }

    return {'code': int(response.userResponse.code),
            'message': str(response.userResponse.message),
            'id': new_org_id,
            }


def update_org(org_info):
    '''
    Creates a new sub-organization.

    See user_client.create_organization()
    for more information.
    '''
    response = user_client.update_organization(**org_info)
    return {'code': response.code,
            'message': response.message
            }


def search_org(org_id, status=1):
    '''
    Searches for a set of organizations.
    Status is 1 for active, 2 for inactive. Other values may be valid

    See user_client.search_organization() for more info


    '''
    orgs = user_client.search_organization(org_id=org_id, portal_id=1,
                                           status=status, type_id=1)

    log.info('organizations: {}'.format(str(orgs)))
    resp = {'yourParentId': orgs.organizationsVO.parentId,
            'yourOrgId': orgs.organizationsVO.orgSearchCriteria.orgId,
            'orgInfo': [{'address': org.addressOne,
                         'name': org.name,
                         'city': org.city,
                         'zip': org.zip,
                         'state': org.state,
                         'status': org.status,
                         'type': org.typeId,
                         'orgId': org.organizationId,
                         }
                        for org in orgs.organizationsVO.organizations]}
    return resp


def get_org(org_id):
    '''
    Returns the information for a particular organization.

    For the purposes of this application, this function is
    only ever used to return the information of the logged in
    user's organization.

    '''
    myOrg = user_client.find_organization(org_id).organizationVO

    return {'address': myOrg.addressOne,
            'name': myOrg.name,
            'city': myOrg.city,
            'zip': myOrg.zip,
            'state': myOrg.state,
            'status': myOrg.status,
            'type': myOrg.typeId,
            'orgId': myOrg.organizationId,
            }


class OrgHandler(BaseHandler):
    @login_required()
    def orgPage(self):
        self.response.out.write(
            template.render(
                os.path.join('template', 'org_tmpl.html'),
                {'username': self.session.get('username'),
                 'version': version_string}))

    @login_required(json_=True)
    def createOrg(self):
        org_info = {}
        try:
            org_info['parent_id'] = self.request.get('parent_id')
            org_info['name'] = self.request.get('name')
            org_info['address'] = self.request.get('address')
            org_info['city'] = self.request.get('city')
            org_info['zip_'] = self.request.get('zip')
            org_info['state'] = self.request.get('state')
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'org_info parameter missing'}))
            self.response.status = 500
            return

        response = create_org(org_info)

        if response['code'] != 200:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': response['message']}))
            self.response.status = 502

        else:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': (
                                'Organization Created: id={}'.format(
                                    response['id']))}))

    @login_required(json_=True)
    def modifyOrg(self, org_id):
        org_info = {}
        try:
            org_info['org_id'] = org_id
            org_info['name'] = self.request.get('name')
            org_info['address'] = self.request.get('address')
            org_info['city'] = self.request.get('city')
            org_info['zip_'] = self.request.get('zip')
            org_info['state'] = self.request.get('state')

        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Missing parameter in "org_info".'}))
            self.response.status = 500
            return

        response = update_org(org_info)
        if int(response['code']) != 200:
            self.response.status = 502

        self.response.out.write(
            json.dumps({'logged_in': True,
                        'message': response['message']}))

    @login_required(json_=True)
    def getOrgs(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': search_org(org_id)}))

    @login_required(json_=True)
    def getOwnOrg(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_org(org_id)}))

    @login_required(json_=True)
    def getParents(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': possible_parents(org_id)}))


org_routes = [
    webapp2.Route(r'/', OrgHandler,
                  handler_method='orgPage', methods=['GET']),
    webapp2.Route(r'/org/', OrgHandler,
                  handler_method='getOrgs', methods=['GET']),
    webapp2.Route(r'/org/', OrgHandler,
                  handler_method='createOrg', methods=['POST']),
    webapp2.Route(r'/org/self', OrgHandler,
                  handler_method='getOwnOrg', methods=['GET']),
    webapp2.Route(r'/org/parent', OrgHandler,
                  handler_method='getParents', methods=['GET']),
    webapp2.Route(r'/org/<org_id>', OrgHandler,
                  handler_method='modifyOrg', methods=['POST']),
]
