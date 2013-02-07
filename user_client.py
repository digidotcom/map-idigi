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

import logging
from os import environ
import webapp2
from suds.client import Client
from suds.sax.element import Element
from role_lists import permission_dict
from custom_exceptions import MapError

wsdl_base = environ['MAP_WSDL_BASE']

USR_URL = '{}UserService?wsdl'.format(wsdl_base)
SUBLEVEL_ACCESS = True

log = logging.getLogger(__name__)


def get_user_client():
    '''
    Returns a soap client object.

    If an object has already been created, we recyle it,
    otherwise, a new one is created and returned.

    '''
    app = webapp2.get_app()
    request = webapp2.get_request()

    username = request.registry['session'].get('username')
    password = request.registry['session'].get('password')
    user_key = 'user_client:{}'.format(username)

    # check if we already have the client
    user_client = app.registry.get(user_key)
    if not user_client:
        user_client = Client(USR_URL, cache=None)
        user_client.add_prefix(
            'srv', "http://service.user.core.mtrak.digi.com")
        user_client.add_prefix(
            'vo', "http://vo.user.core.mtrak.digi.com/xsd")

        app.registry[user_key] = user_client

    user_client.set_options(soapheaders=(
        Element('username').setText(username),
        Element('password').setText(password)))

    return user_client


def get_user_group_map(org_id):
    '''
    Returns a dictionary with the names of roles mapped to
    to their respective user groups' IDs.

    If this map exists in the registry it is returned
    immediately, otherwise it is created on the fly and stored.

    '''
    app = webapp2.get_app()
    request = webapp2.get_request()

    client = get_user_client()

    org_id = int(org_id)

    logging.debug('findUserGroupByOrgId id=({})'.format(org_id))
    response = client.service.findUserGroupByOrgId(org_id)

    user_group_map = {'base': None,
                      'user': None,
                      'asset': None,
                      'track': None,
                      'device': None,
                      'geofence': None,
                      'route': None,
                      }

    try:
        for ugVO in response.userGroupVO:
            if 'roles' in ugVO:
                for role in ugVO.roles:
                    if 'permission' in role and role.name in user_group_map:
                        log.debug('found role: {}'.format(role.name))
                        user_group_map[role.name] = ugVO.userGrpId
    except AttributeError:
        log.error('No UserGroupVO attribute in response')
        raise MapError(response.userResponse.code,
                       response.userResponse.message)

    # Only return groups which exist for this organization
    for group, group_id in user_group_map.items():
        if group_id is None:
            log.error('deleting role {} from user_group_map'.format(group))
            del user_group_map[group]

    return user_group_map


def _make_VO(namespace, name, client=None, **kwargs):
    '''
    Creates a Suds SOAP value object.

    namespace = string
    name = string

    '''
    if not client:
        client = get_user_client()

    vo_str = namespace + ':' + name
    vo = client.factory.create(vo_str)
    for key in kwargs:
        vo[key] = kwargs[key]

    return vo


def search_organization(org_id=None, portal_id=None, name=None,
                        type_id=None, status=None,
                        min_=1, max_=10000000):
    '''
    Returns organizations given specific criteria.

    Searching first looks for a portal_id, org_id, or name,
    in that order. Only one of these three criteria can be searched
    at the same time. The other two will be ignored.

    Next, the search can be paired down by searching by a specific
    type_id and/or status. Neither of these fields are required.

    '''
    client = get_user_client()
    orgSearchVO = _make_VO('vo', 'OrgSearchCriteriaVO')

    orgSearchVO.orgId = org_id
    orgSearchVO.portalId = portal_id
    orgSearchVO.orgName = name
    orgSearchVO.orgType = type_id
    orgSearchVO.status = status
    orgSearchVO.minRange = min_
    orgSearchVO.maxRange = max_

    response = client.service.searchOrganization(orgSearchVO)
    return response


def find_organization(org_id):
    '''
    Uses an organization's ID to return its information.

    '''
    client = get_user_client()

    response = client.service.findOrganizationById(org_id)
    return response


def search_user(org_id=None, portal_id=None, min_=1, max_=100):
    '''
    Searches for all users in a given organization.

    '''
    if SUBLEVEL_ACCESS:
        portal_id = 1

    client = get_user_client()
    userSearchVO = _make_VO('vo', 'UserSearchCriteriaVO')

    userSearchVO.minRange = min_
    userSearchVO.maxRange = max_
    userSearchVO.portalId = portal_id
    userSearchVO.orgId = org_id

    response = client.service.searchUser(userSearchVO)
    log.info(response)
    return response


def create_user(user_name, password, user_group_names,
                org_id, f_name, l_name, m_name=None, email=None):
    '''Creates a new user in a given organization.'''
    logging.info(org_id)
    client = get_user_client()
    userInfoVO = _make_VO('vo', 'UserInfoVO')
    userLoginVO = _make_VO('vo', 'UserLoginVO')

    userInfoVO.firstName = f_name
    userInfoVO.lastName = l_name
    userInfoVO.middleName = m_name if m_name else ''
    userInfoVO.email1 = email if email else 'jane.doe@company.net'
    userInfoVO.organizationId = org_id
    userInfoVO.sublevelPermission = True

    userLoginVO.password = password
    userLoginVO.userName = user_name

    user = client.factory.create('ns2:UserProfileVO')
    user.userInfo = userInfoVO
    user.userLogin = userLoginVO
    user.userGroupId = []
    logging.info(user_group_names)
    user_group_map = get_user_group_map(org_id)
    for name in user_group_names:
        try:
            user.userGroupId.append(user_group_map[name])
        except KeyError, e:
            raise

    response = client.service.createUser(user)
    return response


def update_user(user_id, user_name, password, user_group_names,
                org_id, f_name, l_name, m_name=None, email=None):
    '''Takes an existing user and updates their information.'''
    client = get_user_client()
    userInfoVO = _make_VO('vo', 'UserInfoVO')
    userLoginVO = _make_VO('vo', 'UserLoginVO')

    userInfoVO.firstName = f_name
    userInfoVO.lastName = l_name
    userInfoVO.middleName = m_name if m_name else '_'
    userInfoVO.email1 = email if email else 'jane.doe@company.net'
    userInfoVO.organizationId = org_id
    userInfoVO.userId = user_id

    userLoginVO.password = password
    userLoginVO.userName = user_name

    user = client.factory.create('ns2:UserProfileVO')
    user.userInfo = userInfoVO
    user.userLogin = userLoginVO
    for name in user_group_names:
        user.userGroupId.append(get_user_group_map(org_id)[name])

    response = client.service.updateUser(user)
    return response


def activate_user(user_id):
    '''
    Activate a user in the system.

    This effectively changes their status to '1'

    '''
    client = get_user_client()

    response = client.service.activateUser(user_id)
    return response


def deactivate_user(user_id):
    '''
    Deactivates a user of the service

    This effectively changes their status to '2'

    '''
    client = get_user_client()

    response = client.service.deActivateUser(user_id)
    return response


def create_new_user_group(parent_id, name, client=None):
    if not client:
        client = get_user_client()

    orgVO = _make_VO('vo', 'OrganizationVO', client=client)
    orgVO.parentId = parent_id
    orgVO.name = name
    orgVO.portalId = 1

    response = client.service.createUserGroup(orgVO)
    return response


def add_user_to_user_group(user_id, user_group_id, org_id):
    '''
    Adds a user to a group.

    A user can be in more than one group.

    '''
    client = get_user_client()

    userGroupOrgVO = _make_VO('vo', 'UserGroupOrgVO')
    userGroupOrgVO.userId = user_id
    userGroupOrgVO.usrGrpId = user_group_id
    userGroupOrgVO.orgId = org_id

    response = client.service.addUserToUserGroup(userGroupOrgVO)
    return response


def remove_user_from_user_group(user_id, user_group_id, org_id):
    '''Removes a user from a user group.'''
    client = get_user_client()

    userGroupOrgVO = _make_VO('vo', 'UserGroupOrgVO')
    userGroupOrgVO.userId = user_id
    userGroupOrgVO.usrGrpId = user_group_id
    userGroupOrgVO.orgId = org_id

    response = client.service.removeUserFromUserGroup(userGroupOrgVO)
    return response


def add_permission_to_role(role_id, permission_name):
    '''Adds a permission (ability to make a function call) to a role.'''
    client = get_user_client()

    permissionVO = _make_VO('vo', 'PermissionVO')
    permissionVO.name = permission_name

    response = client.service.addPermissionToRole(role_id, permissionVO)
    return response


def remove_permission_from_role(role_id, permission_id):
    '''Removes a permission from a given role.'''
    client = get_user_client()

    permissionVO = _make_VO('vo', 'PermissionVO')
    permissionVO.name = permission_id

    response = client.service.removePermissionFromRole(role_id, permission_id)
    return response


def add_role_to_group(role, parent_id, user_group_id, client=None):
    '''Adds a role to a group'''
    if not client:
        client = get_user_client()

    ugVO = _make_VO('vo', 'UserGroupVO', client=client)
    ugVO.userGrpId = user_group_id
    ugVO.roles = [role]

    response = client.service.addRolesToUserGroup(ugVO)
    return response


def remove_role_from_user_group(role_id, org_id, user_group_id):
    '''Removes the role from a particular user group.'''
    client = get_user_client()

    userGroupOrgVO = _make_VO('vo', 'UserGroupOrgVO')
    userGroupOrgVO.roleId = role_id
    userGroupOrgVO.orgId = org_id
    userGroupOrgVO.usrGrpId = user_group_id

    response = client.service.removeRolesFromUserGroup(userGroupOrgVO)
    return response


def get_user_group_by_group_id(user_group_id):
    '''Request information about a specific user group'''
    client = get_user_client()

    response = client.service.getUserGroup(user_group_id)
    return response


def create_organization(parent_id, name, address, city, zip_, state,
                        status=1):
    '''
    Creates an organization

    Organizations are self-contained entities under which
    a set of users, assets, devices, and other objects of
    the service can interact.

    Organizations have a heirarchical nature. That is, if
    you make an organization with a parentId of your own,
    you will be able to view aspects of the new organization,
    but members of the new organization will be unable to
    access any data from your own. To create your own
    subordinate org, set parent_id equal to your own.

    '''
    client = get_user_client()
    orgVO = _make_VO('vo', 'OrganizationVO')
    orgVO.addressOne = address
    orgVO.city = city
    orgVO.zip = zip_
    orgVO.state = state
    orgVO.name = name
    orgVO.status = status

    # Just some housekeeping:
    #  -typeId signifies that this is an organization
    #     (as opposed to a user group. try
    #      user_client.getOrgTypes() for more info)
    #  -portalId is assigned per company. In this
    #     sample we are all portalId=1
    orgVO.parentId = parent_id
    orgVO.typeId = 1
    orgVO.portalId = 1
    orgVO.contact = ['PlaceHolder']

    response = client.service.createOrganization(orgVO)
    return response


def update_organization(org_id, name, address, city, zip_, state):
    '''
    Modifies an existing organization

    '''
    client = get_user_client()
    orgVO = _make_VO('vo', 'OrganizationVO')
    orgVO.addressOne = address
    orgVO.city = city
    orgVO.zip = zip_
    orgVO.state = state
    orgVO.name = name

    orgVO.organizationId = org_id
    orgVO.typeId = 1
    orgVO.portalId = 1
    orgVO.status = 1
    orgVO.contact = _make_VO('vo', 'ContactVO')
    orgVO.contact.contactTypeId = 1
    orgVO.contact.description = ''
    response = client.service.updateOrganization(orgVO)
    return response


def activate_organization(org_id):
    ''' Deactivates and organization.'''
    client = get_user_client()
    response = client.service.activateOrganization(org_id)
    return response


def deactivate_organization(org_id):
    ''' Deactivates and organization.'''
    client = get_user_client()
    response = client.service.deActivateOrganization(org_id)
    return response


def create_permissions(parent_id):
    '''
    Creates new user groups, each with one role.

    User Groups are how the service defines user permissions.
    Each User Group contains roles, which themselves contain
    permissions. Users can belong to more than one group, and
    groups can contain many users. For the sake of this sample
    application, we define a set of pre-existing user group
    roles in role_lists.py

    '''

    responses = [None] * len(permission_dict.keys())
    client = get_user_client()
    for i, p_list in enumerate(permission_dict):
        create_permissions_helper(p_list, parent_id, responses, i, client)

    for success, resp in responses:
        if not success:  # Note: This can obviously only raise one error
            raise resp

    return parent_id


def create_permissions_helper(p_list, org_id, responses, i, client):
    '''
    Creates one user group and adds one role to that group

    '''
    try:
        #create a new user group
        name = str(p_list)
        resp = create_new_user_group(org_id, name, client=client)

        try:
            user_group_id = int(resp.organizationVO.organizationId)
            log.warning('user_grou_id made for {} is {}'.format(
                p_list, user_group_id))
        except AttributeError:
            log.exception('missing organizationVO {}'.format(str(resp)))
            raise

        #create a role and fill it with permissions
        role = _make_VO('vo', 'RoleVO', client=client)
        role.name = name

        for permission in permission_dict[p_list]:
            pVO = _make_VO('vo', 'PermissionVO', client=client)
            pVO.name = permission
            role.permission.append(pVO)

        #Add a new role to that group
        role_response = add_role_to_group(role, org_id, user_group_id, client)
        responses[i] = (True, role_response)
    except Exception, e:
        import traceback

        responses[i] = (False, e)
