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

class MapError(Exception):
    '''
    Generic exception for dealing with errors from MAP soap requests
    
    Attributes:
        code -- Numeric error code
        message -- Error description
    '''
    def __init__(self, code, message):
        self.code = code
        self.message = message