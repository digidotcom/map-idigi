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
import webapp2
import user_client
from base import version_string, BaseHandler, login_required
from custom_exceptions import MapError

log = logging.getLogger(__name__)

#####
# Internal functions which implement login functionality


def search_users(org_id):
    '''
    This function returns information about all users
    in a given organization.

    the group_name 'base' is used because all users we create
    have a user group which is mapped in the datastore to 'base'
    '''

    user_info = []
    response = user_client.search_user(org_id=org_id)

    if not response.userProfilesVO or \
            'userProfiles' not in response.userProfilesVO:
        return []

    group_map = user_client.get_user_group_map(org_id)

    for user in response.userProfilesVO.userProfiles:
        u = {}
        u['user_id'] = user.userInfo.userId
        u['org_id'] = user.userInfo.organizationId
        u['sublevelPermission'] = user.userInfo.sublevelPermission
        u['first_name'] = user.userInfo.firstName
        u['last_name'] = user.userInfo.lastName
        u['middle_name'] = user.userInfo.middleName
        u['email'] = user.userInfo.email1
        u['status'] = user.userLogin.status
        u['user_name'] = user.userLogin.userName
        if user.userInfo.organizationId == org_id:
            u['user_groups'] = [key for key in group_map
                                if group_map[key] in user.userGroupId]
        else:
            u['user_groups'] = [('Please view in organization '
                                 '{} to access').format(u['org_id'])]
        user_info.append(u)

    return user_info


def create_user(user_info):
    '''
    This function takes in user_info, which contains the
    user's personal and login info.

    It parses this information and passes it to
    user_client.create_user.

    Returns the response from user_client.create_user.

    '''

    user_name = user_info['user_name']
    password = user_info['password']
    user_group_names = user_info['user_group_names']
    org_id = user_info['org_id']
    f_name = user_info['first_name']
    l_name = user_info['last_name']
    m_name = user_info['middle_name']
    email = user_info['email']

    if not 'base' in user_group_names:
        user_group_names.append('base')

    try:
        response = user_client.create_user(
            user_name, password, user_group_names,
            org_id, f_name, l_name, m_name, email)
    except MapError as e:
        return {'code': e.code,
                'message': e.message,
                }

    return {'code': response.userResponse.code,
            'message': response.userResponse.message,
            }


def update_user(user_info):
    '''
    This function takes in user_info, which contains the
    user's personal and login info.

    It parses this information and passes it to
    user_client.update_user.

    Returns the response from user_client.update_user.

    '''
    user_name = user_info['user_name']
    password = user_info['password']
    user_group_names = user_info['user_group_names']
    org_id = user_info['org_id']
    f_name = user_info['first_name']
    l_name = user_info['last_name']
    m_name = user_info['middle_name']
    email = user_info['email']
    user_id = user_info['user_id']

    if not 'base' in user_group_names:
        user_group_names.append('base')

    response = user_client.update_user(
        user_id, user_name, password, user_group_names,
        org_id, f_name, l_name, m_name, email)

    return {'code': response.code,
            'message': response.message,
            }


def activate_user(user_id):
    '''
    Takes in the user ID and passes it to user_client.activate_user,
    then returns the response.

    '''
    response = user_client.activate_user(user_id)

    return response


def deactivate_user(user_id):
    '''
    Takes in the user ID and passes it to user_client.deactivate_user,
    then returns the response.

    '''
    response = user_client.deactivate_user(user_id)

    return response


def check_permission(permission_data, user_id):
    '''
    Takes in permission_data and user_id and passes information to
    user_client.check_permission, then parses and returns the result
    as a dictionary.

    '''
    operationOrgId = permission_data['operationOrgId']
    permissionName = permission_data['permissionName']
    sublevelPermission = permission_data['sublevelPermission']
    userOrgId = permission_data['userOrgId']

    response = user_client.check_permission(operationOrgId, permissionName,
                                            sublevelPermission,
                                            user_id, userOrgId)

    response_dict = {'permission': response.permission,
                     'code': response.userResponse.code,
                     'message': response.userResponse.message,
                     }

    return response_dict


def add_user_to_group(user_id, user_group_id, org_id):
    '''
    Takes in the group and user ID's to be associated,
    passes then to user_client.add_user_to_group, and returns
    the result.

    '''
    response = user_client.add_user_to_user_group(user_id,
                                                  user_group_id, org_id)

    return response


def remove_user_from_group(user_id, user_group_id, org_id):
    '''
    Takes in the group and user ID's to be un-associated,
    passes then to user_client.remove_user_from_group, and returns
    the result.

    '''
    response = user_client.remove_user_from_user_group(user_id,
                                                       user_group_id, org_id)
    return response


def create_user_group(parent_id):
    '''
    Takes in an oganization Id, makes up some stuff necessary
    for creating a new user group, and passes everything to
    user_client.create_user_group then returns the response.

    This could probably be implemented better....
    '''

    portalId = 1
    parentId = 1

    response = user_client.create_user_group(parentId, portalId)

    return response


def get_groups_by_org_id(org_id):
    '''
    Takes in an organization ID and returns a list of all
    groups associated with it.

    '''

    user_dict = user_client.get_user_group_map(org_id)

    return user_dict.keys()


#####
# Web services handlers


class UserHandler(BaseHandler):
    @login_required()
    def userPage(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            template.render(
                os.path.join('template', 'user_tmpl.html'),
                {'username': self.session.get('username'),
                 'org_id': org_id,
                 'version': version_string}))

    @login_required(json_=True)
    def getUserGroups(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': get_groups_by_org_id(org_id)}))

    @login_required(json_=True)
    def createUser(self):
        user_info = {}
        try:
            user_info['first_name'] = self.request.get('first_name')
            user_info['last_name'] = self.request.get('last_name')
            user_info['middle_name'] = self.request.get('middle_name')
            user_info['email'] = self.request.get('email')
            user_info['org_id'] = int(self.request.get('org_id'))
            user_info['password'] = self.request.get('password')
            user_info['user_name'] = self.request.get('user_name')
            user_info['user_group_names'] = self.request.get_all(
                'user_group_names')
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'user_info parameter missing'}))
            self.response.status = 500
            return
        except ValueError as e:
            # This is easy to get out of step with reality.
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'organization id is not an integer'}))
            self.response.status = 502
            return

        try:
            resp = create_user(user_info)
        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'unable to find user group: '
                            + e.message}))
            self.response.status = 502
            return

        if int(resp['code']) != 200:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': resp['message']}))
            self.response.status = 502

        else:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Success!'}))

    @login_required(json_=True)
    def getUsers(self):
        request = webapp2.get_request()
        org_id = request.registry['session'].get('organization_id')
        self.response.out.write(
            json.dumps({'logged_in': True,
                        'payload': search_users(org_id)}))

    @login_required(json_=True)
    def modifyUser(self, user_id):
        user_info = {}
        try:
            user_info['first_name'] = self.request.get('first_name')
            user_info['last_name'] = self.request.get('last_name')
            user_info['middle_name'] = self.request.get('middle_name')
            user_info['email'] = self.request.get('email')
            user_info['org_id'] = int(self.request.get('org_id'))
            user_info['password'] = self.request.get('password')
            user_info['user_name'] = self.request.get('user_name')
            user_info['user_id'] = user_id
            user_info['user_group_names'] = self.request.get_all(
                'user_group_names')

        except KeyError, e:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Missing parameter "user_info".'}))
            self.response.status = 500
            return
        except ValueError as e:
            # This is easy to get out of step with reality.
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'organization id is not an integer'}))
            self.response.status = 502
            return

        resp = update_user(user_info)

        if int(resp['code']) != 200:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': resp['message']}))
            self.response.status = 502

        else:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': 'Success!'}))

    @login_required(json_=True)
    def activateUser(self, user_id):
        try:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': str(activate_user(user_id))}))
        except KeyError, e:
            self.abort(404, "User ID not found.")

    @login_required(json_=True)
    def deactivateUser(self, user_id):
        try:
            self.response.out.write(
                json.dumps({'logged_in': True,
                            'message': str(deactivate_user(user_id))}))
        except KeyError, e:
            self.abort(404, "User ID not found.")

user_routes = [
    webapp2.Route(r'/', UserHandler,
                  handler_method='userPage', methods=['GET']),
    webapp2.Route(r'/user', UserHandler,
                  handler_method='createUser', methods=['POST']),
    webapp2.Route(r'/user', UserHandler,
                  handler_method='getUsers', methods=['GET']),
    webapp2.Route(r'/user/<user_id>', UserHandler,
                  handler_method='modifyUser', methods=['PUT']),
    webapp2.Route(r'/user/group', UserHandler,
                  handler_method='getUserGroups', methods=['GET']),
    webapp2.Route(r'/user/<user_id>/activate', UserHandler,
                  handler_method='activateUser', methods=['PUT']),
    webapp2.Route(r'/user/<user_id>/deactivate', UserHandler,
                  handler_method='deactivateUser', methods=['PUT']),
]
