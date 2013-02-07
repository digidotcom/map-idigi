<head>
    <link href="hilite.css" rel="stylesheet" type="text/css">
</head>
# Introduction to MAP and the Sample Applications
## What is MAP for iDigi?
## What is the intent of this guide?
This guide acts as an introduction to interacting with the Mobile Assets API in an effective and useful manner. It uses a suite of sample applications to show the functionality of the API and exemplify some common workflows and idioms. This guide does not provide a full overview of the API, nor does it deal with obtaining MAP-enabled devices or device troubleshooting. For more detailed information about the MAP API please see the MAP User Guide. For more help with setting up your device to work with MAP please see the Getting Started Guide. Both of these are available at <https://map.idigi.com>.

## Why are the sample applications written in Python?
Python's available libraries, interactive nature, and Google App Engine supoort allowed us to rapidly develop the sample applications. Most of the code in the sample applications are intentionally straightforward, but Python's syntax makes the logic of the code especially clear.

# SOAP, Libraries, and Useful Tools
Simple Object Access Protocol is a mature protocol for exchanging web services information, generally using XML over HTTP. In general, MAP uses the Remote Procedure Call style of SOAP communication; that is, calls to the MAP API act like function calls and responses from MAP can often be treated as a response to the function invocated.

For these sample applications we are using a library for Pyton called [Suds][suds]. Like SOAP libraries for different languages, Suds parses SOAP messages into native Python data structures. To see the raw XML data that has been sent or received there are a few options. If you have downloaded the sample applcations and have them hosted on your own Google App Engine account, you can view the application logs at <http://appengine.google.com>, including all messages sent and received. If you are using Suds locally or in an interactive session, any messages can be viewed by using `print client.last_sent()` and `print client.last_received()` on your client object.

[suds]: https://feorahosted.org/suds/wiki/Documentation

SOAP libraries and documentation for using them are available in most languages. The general procedure for using a SOAP library is to use the WSDL's provided by a service to create a set of objects representing the objects defined in the WSDL. Communicating with the service is then conducted by filling in these objects with the required data, using the SOAP library to convert the objects into XML and send the request.

## Anatomy of a SOAP message
Each SOAP message is composed of the usual XML version string followed by the SOAP namepsace for the specific service in use. Next comes the SOAP header and body. According to the specification the header is optional, but with MAP we usually use the header contain credential informtion. An example SOAP message:

    :::xml
    <?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope xmlns:ns0="http://vo.atms.core.mtrak.digi.com/xsd"
     xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/"
     xmlns:ns2="http://service.atms.core.mtrak.digi.com"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
        <SOAP-ENV:Header>
            <username>person</username>
            <password>FoobarbaZ</password>
        </SOAP-ENV:Header>
        <ns1:Body>
            <ns2:stopTracking>
                <ns2:args0>
                    <ns0:assetId>31</ns0:assetId>
                </ns2:args0>
            </ns2:stopTracking>
        </ns1:Body>
    </SOAP-ENV:Envelope>

## Credentials using SOAP headers
The way that MAP currently authenticates its users is by using the SOAP headers to retain username and password information. In each client file, the username and password of a specific user is added to the headers of the client. Future versions of MAP will support cookie authentication.


# Structure of the Sample applications
Most of the code relevant to this guide is contained in one of the \*\_client.py files in the root directory. There is one of these files for each of the WSDLs defining the MAP API. Very little application logic happens in these files, they are mostly just an interface layer between the application and MAP, but they are very useful for seeing how to interact with MAP.

Files in the application/ directory are where the application logic happens for each segment of the application. They define the restful API for the sample applications.

The static/ directory holds all of the publicly available resources, such as images, javascript, and css. These are not of particular importance to this guide.

The template/ directory holds the HTML templates for each page.

The suds/ and ndb/ directories are just libraries that need to be included with the application. Suds is the external library used for interacting with SOAP requests, and ndb is a patch for a known bug in Google App Engine.

# Login Service
The following calls are to the Login Service at <https://map.idigi.com/services/LoginService?wsdl>
They follow the functions found in lgn\_client.py

## Authentication
The MAP service itself doesn't currently have sessions or timeouts when it comes to user authentication; every request needs to have proper credentials. However, the *authenticate* method is an easy way to check if a user's credentials are correct when building an application on top of MAP. *authenticate* requires a username and a password, and on success will return a UserProfileVO containing the user's personal information and their account status.

### Authenticating Other Users
It should be noted here that *authenticate* requires no credentials to run (i.e. it can be executed without having a username or password in the header of the request), and that any user can call *authenticate* with any other user's username and password as arguments.

## Credential Management
MAP comes with a few ways to create the underlying implementation for an application's password management.

### Changing a password
The *changePassword* method takes as arguments the user's old password and their new password. This is for times when a user wants to change their password and knows their old password.

### Resetting a password
The *resetPassword* method takes a *SecurityQuestionVO*, which is simply three question-answer pairs, a username, and a new password. This can be used when a user needs a new password but has forgotten their old one. Note that there are other methods of changing a user's password, but that this is the only method MAP provides for a user to change their own password.

### Security questions
As mentioned in the last section, MAP can store security questions and answers for each user. These questions are not necessary if an application on top of MAP has its own password management system, but they are necessary to change the password of a user using MAP's own password management. The methods for interacting with security questions are as follows:

* *createSecurityQuestion*: Sets the given question-answer pairs as the user's password management questions
* *validateSecurityQuestion*: Checks that the given password management questions are correct for a given user
* *getSecurityQuestion*: Returns the questions only for a given user.

*getSecurityQuestion* is likely a necessary call to make before using either *validateSecurityQuestion* or resetPassword. The call's result can be used to fill in the *reminderQuestion* fields in the *SecurityQuestionVO*.

# Device Management Service
The following calls are to the Device Management Service at <https://map.idigi.com/services/DeviceManagementService?wsdl>
They follow the functions found in devcie\_client.py

## Devices
There are a number of devices able to communicate with MAP for iDigi, including the Digi X5R and xTrak3 devices. In MAP, each type of device has it's own deviceType number. To view this type, use the searchDeviceType call with a status of 1.

### Adding devices
Adding a Device to MAP is accomplished through the *provisionDevice* call. Before provisioning a device, make sure that it is not already provisioned in iDigi, as this will cause an error to occur. This call requires:

* *deviceType*: an integer representing the type of MAP enabled device.
* *mobileOperator*: an integer representing the device's mobile carrier. For most users, this field is not required to be accurate, but it is necessary.
* *mobileNumber*: a string representing the device's cellular number.
* *organizationId*: The ID of the organization the device will be associated with. See the Organizations subheader of User Management Service for more info.
* *serial*: A unique, user-provided *identifier* for the device.

In addition to these fields, the *provisionDevice* call may also need a *macAddress* or *IMEI* field, depending on the type of device being provisioned.

### Searching for devices
All devices which have been provisioned in a given organization can be seen using the *searchDevice* call with the correct *organizationId* filled in. To search for a specific device, use the getDevice call with an *organizationId* along with either a device's ID or its serial.

## Device configuration
Devices have many configuration options which control how they communicate with MAP and what information they provide.

### Finding a device's current config
Retreiving a device's configuration can be accomplished using the *getDeviceConfiguration* call and supplying the device's serial. Only configurations that have been set are returned from this call, so a new device will respond with a message of "No record found."

### Changing a device's configuration
The most straightforward way to configure a device is to request the device type's default configuration and edit that structure. By configuring a device like this, it is easier to ensure that the message will be correctly formed and that only options available for your specific device are sent. The way that the sample applications deal with configuring a device are as follows:

1. Query MAP for the default configuration for a device of the correct type using getDeviceTypeConfiguration
1. Query MAP for the current configuration of a specific device--if it exists--using getDeviceConfiguration with the device's serial
1. Merge the two configurations by replacing features in the default configuration with those in the device's current configuration
1. Present this information to the user as a web form
1. Parse the user's changes to the web form and revert them back into a the data structure that MAP requires. The last three steps are in applications/config.py
1. Send the newly created configuration to MAP using the *updateDeviceConfiguration* call

If you are using the sample applications as a guide for building your own applications, note that almost all of the comlpexity of this process is contained in steps 4 and 5. Programmatically editing the default configuration and sending it to the device is easy, but exposing it as a user interface is much more complicated. The general use case is to edit a device's configuration once and then likely never again for the lifetime of the device, so querying MAP for the default configuration and editing it directly is likely the best choice for an application's needs.

# Fleet Management Service
The following calls are to the Fleet Management Service at <https://map.idigi.com/services/FleetManagementService?wsdl>
They follow the functions found in fms\_client.py

## Assets
Assets are a first-class object in MAP in that they can be created, deleted, edited, and queried directly. An asset is anything which a device is connected to, such as a truck, a train car, or a package. Assets are important because they allow users to access the most interesting features of MAP.

### Creating and updating
Creating a new asset and modifying an existing asset are very similar, and use the *createAsset* and *updateAsset* calls respectively. The basic information necessary to create an asset is:

* *assetTypeVO*: This is an embedded object within an *asssetVO*. The different types of assets created so far can be found using the *searchAssetType* call with an empty *assetTypeVO*.
* *deviceSerial*: The user-defined serial for the device
* *identificationNumber*: A unique number identifying the asset
* *name*: A text string identifying the asset
* *status*: The current status of the asset represented as an integer. While this field must contain a valid integer (1-5), it does not actually affect the status of the asset when created. For most purposes it is okay to just insert a 1 in this field.
* *installationDate*: A specifically formatted date string. See the make\_time\_string() and make\_time\_from\_string() function calls within fms\_client.py for more information, and note that they use the same formatting options as the strftime and strptime calls in C.

### Searching
Searching for assets is generally done using either the *searchAsset* or *getAsset* call. *searchAsset* takes a *SearchAssetVO* as an argument, to which can be supplied further information to limit the search. The only fields that must be supplied are the fromLimit and toLimit, which limit the nubmer of assets returned from the search. The sample applications do not showcase any searches more specific than searching for all assets available, but the process is straightforward.

*getAsset* takes an *assetIdVO* and will return only a specific asset. An asset's *assetId* is the number assigned to it by MAP when it was first created, not to be confused with the asset's *identificationNumber*.

### Deleting
Deleting an asset with *deleteAsset* is almost identical to using *getAsset* discussed above. Deleting an asset will disassociate the asset from its respective device, but will not unprovision the device from MAP or remove the device from iDigi. At this time there is no way do delete a device from MAP.

## Geofences
Geofences allow assets to be contained within a geographical region. They are separate objects from assets and the geofence-asset relationship is many-to-many; many geofences can be applied to a single asset, and many assets may have reference to a single geofence. For the purposes of the sample applications only one geofence is allowed per asset, but this is a self-imposed limitation.

### Creating a geofence
To create a geofence, use the *createGeofence* call with a *GeofenceVO*. *GeofenceVOs* have a nubmer of required fields:

* *geofenceName*: The name of the geofence
* *geofenceType*: The ID of the geofence type. Geofence types can be searched using the getGeofenceTypesList call with zero arguments
* *organizationId*: The ID of the organization the geofence should be added to. Your own organizationId is available by calling LoginService.authenticate using your own credentals
* *geofenceGeometry*: Geofences take a very specific geometry format. The format is:
    "POLYGON((long1 lat1, long2 lat2, ... , longN, latN, long1 lat1))"
For each point, longitude comes before latitude, and the coordinates are separated by a space. each point is separated by a comma, and the entire structure is surrounded by "POLYGON((...))". Also note that the first point must be the same as the last point.

### Attaching geofences to assets
Applying a geofence to an asset can be accomplished using the *applyGeofence* call. This call takes an *assetGeofenceVO*, which contains a single assetId as well as a list of *geofenceIds*. as seen in apply\_geofence() in fms\_client.py, the sample applications do not make use of multiple geofences per asset, but adding more geofences would simply involve adding more geofences to the list.

## Other Asset Data
MAP stores other useful information about each asset's whereabouts and activities.

### On-Board Diagnostics (OBD-II) Data
To access information about the state of a vehicle, use the *getDiagnosticData* call with the correct *deviceSerial*. The *deviceSerial* is the serial of the device attached to an asset. Note that not all types of devices support the collection of OBD-II data, and the device may have to be configured correctly before it is able to collect this information.

### Asset Tracking and Alert data
Correctly configured and active assets are continually sending data about their state to MAP. Textual representations of this binary data can be accessed using the *getAsssetTracksByAssetId* and *getAssetAlertsByAssetId* calls. each take in an *FMSInputVO*, and require a *fromLimit*, *toLimit*, *fromTime*, and *toTime*. Just like the asset's *installationDate*, the *fromTime* and *toTime* are required to be a specifically formatted string which can be created using the function make\_time\_string() in fms\_client.py. The only difference between the two calls is the severity of the message.

### Polling and Tracking an Asset
The *pollAsset*, *startTracking*, and *stopTracking* commands all take an *assetIdVO* as their only argument. *pollAsset* will give a short message about the state of the asset. *startTracking* and *stopTracking* control whether the asset should be sending up tracking data to MAP. It is important to note that the startTracking command should not be issued if the device is not correctly configured for tracking. See the [Getting Started Guide][gsg] for more info.


# User Management Service
The following calls are to the User Service at <https://map.idigi.com/services/UserService?wsdl>
And follow the functions found in user\_client.py

## Organizations
An organization is the highest-level concept of user management in MAP. Many users, user groups, assets, devices, and geofences can all interact with each other if they are in the same organization. Organizations follow a tree structure, and every organization has a parent organization. For instance, if you used the sign-up application at <https:map.idigi.com/signup/>, then your organization is a sub-organization of the root. Users in an organization cannot interact with their parent organizations, but they may interact with their sub-organizations if their sublevelPermision is set to true.

### Creating an Organization
Organizations can be created using the *createOrganization* call and providing a filled-out *organizationVO*. An *organizationVO* contains the following important fields:

* *address*, *city*, *state*, and *zip*: Pieces of the organizatoin's address. These are not necessary
* *status*: An integer. 1 means 'active', and 2 means 'inactive'. 1 is almost always the correct choice, because an inactive organization cannot be interacted with.
* *parentId*: the parentId signifies which organization will be the parent of the newly created organization. To make a sub-organization, just use your own organization's ID.
* *typeId*: organizations come in four types, represented by the integers 1-4.
    * 1: Organization
    * 2: Service Provider
    * 3: Company
    * 4: User Group
    When creating a new organization, always choose 1. User Groups are described below, but there is never a reason to create an organization of type 4 because there is a separate *createUserGroup* call.
* *portalId*: portalId is a value assigned per-company. If you created your account using the signup page, then always choose the integer 1 when encountering this field.
* *contact*: The contact field is not necessary when creating an organization, but it is necessary when modifying one. To create a contact, insert a filled-out *ContactVO* within this field.

### Searching for Organizations
The *searchOrganization* call is one of the most subtle in the API. As is described in search\_organization() within user\_client.py, here are the rules for searching organizations:

1. MAP searches for a *portalId*, *orgId*, or *name*, *in that order*. If one of these fields is found, then the other two are disregarded. One of these is required.
1. Next, the *typeId* and *status* of the organization can be used to pare down the search results. Searching with a *typeId* of 1 will only return "real" organizations, and searching with a *status* of 1 will disregard disabled organizations. Neither of these fields is required.
1. *minRange* and *maxRange* are used to limit the number of search results. These two fields are always required.

Searching by organization will return all organizations available which are children of the organization given. Notice that this does not include the organization given in the search. Searching by portalId will return all organizations visible to the current user, including their current organization, but beware that searching by portalId may take a longer time to execute.

Finding a specific organization can be accomplished using the *findOrganizationById* call. It takes an integer as its argument--not a SOAP object--and returns the information for that specific organization.

## Users
In MAP, a user is a set of credentials which are tied to some metadata. More importantly, each user is associated with a specific set of permissions. Depending on the use cases deemed important for an application built on MAP, it may or may not make sense for every user of the application to have their own MAP user with separate credentials and permissions. In the sample applications, users sign in with their MAP credentials and can only interact with API calls that they have permission to make.

### Creating a new user
Creating a new user with *createUser* is similar to the other object creation calls mentioned so far in this guide. Each *UserProfileVO* is made up of the following objects:

* *UserInfoVO*: Contains personal information
* *UserLoginVO*: Contains information about their account
* *UserGroupId*: a list of user groups the user is associated with. See User Groups below for more info.

At a minimum the following fields must be filled to create a user:

* A first, middle, and last name
* A username and password. The username must be unique and a password must be eight characters.
* At least one user group
* An *organizationId*

To allow the user to interact with sub-organizations, their *sublevelPermission* should be set to True.

### Modifying users
Modifying a user through the updateUser call is almost exactly the same as creating a user. One important detail is that it is not sufficient to only send fields that you wish to change. You have to send all fields required for createUser to updateUser as well.

### Activating and Deactivating users
Users cannot be deleted, but they can be deactivated using the *deActivateUser* call with the user's ID. This bars the user from making any API calls and is equivalent to setting their status to 2. The *activateUser* call does the opposite. Be careful: if a user has permission to deactivate other users, they also have the ability to deactivate themselves. It is possible to accidentally deactivate all users in an organization, in which case they will all be locked out!

### Searching for Users
Searching for users is far more straightforward than searching for organizations. Users can provide an *organizationId*, *portalId*, *status*, and/or *userGrpId* to narrow the search. Unlike with *searchOrganization*, these are all additive, so including another field can only narrow the search results. Remember that the current user can always be found by using LoginService.*authenticate*.

## User Groups
User Groups encapsulate the permissions given to users. The way permissions are managed in MAP is that users either do or do not have access to functionality on a per-API-call basis. This lets application developers decide what each user is capable of doing on a very granular level.

### User Groups, Roles, and Permissions
The simplest object in MAP's permission scheme is the *PermissionVO*. A *PermissionVO* contains the name of an API call and an ID. To create a *PermissionVO* the ID is not necessary to provide.

A *RoleVO* contains multiple *PermissionVOs*, along with a name and description. This allows a number of similar calls to be grouped together.

A *UserGroupVO* contains multiple *RoleVOs*. These are the objects which are associated with users. If a *PermissionVO* exists within a *UserGroupVO* that a user is associated with, then that user has permission to make that API call.

### Building a new user group
The steps for creating a new user group are as follows:

1. Create one or a number of *RoleVOs* and populate them with *PermissionVOs*. Each *PermissionVO* needs to contain the full name of an API call, such as 'getGeofenceTypesList' in the name field. The ID field is not required.
1. Create a new user group using the *createUserGroup* call. This call perplexingly takes an *OrganizationVO*. Only the *organizationId*, *portalId*, and *name* fields are required.
1. Attach the role(s) to the user group using the *addRoleToUserGroup* call. This call takes a *UserGroupVO* as an argument. The *UserGroupVO* is composed of a *userGroupID* and a list of *RoleVO* literals.

It is important to note that roles in MAP are not first-class objects. They cannot be added to MAP other than inside of a user group, and they cannot be searched for. This is why when creating a new user group it is easiest to just create and add Roles to the user group on-the-fly.

### Creating a Workable Permission Scheme
In the sample applications, we took the following measures to create a realistic permission scheme:

* All possible API calls are sorted into lists in role\_lists.py. These lists are in no way special; they are just what we as developers decided might be useful groupings.
* Every time an organization is created, we also create a user group for each group of permissions. This can be seen in create\_permissions() in user\_client.py
* Each user group only has one role, composed of all of the permissions in its respective role\_list. This is for simplicity.
* The application keeps a map of user\_group\_name-to-user\_group\_ids. The code for this can be seen in get\_user\_group\_map() in user\_client.py
* When creating or modifying a user, the user group id's are translated into meaningful names
