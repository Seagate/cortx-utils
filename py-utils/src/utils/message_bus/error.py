#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

from cortx.utils import errors

# common message_bus error codes
ERR_LEADER_NOT_AVAILABLE = 0x2001
ERR_CLIENT_NOT_FOUND = 0x2002
ERR_INVALID_CLIENT_TYPE = 0x2003
ERR_INVALID_BROKER_TYPE = 0x2004

# message_type related
ERR_UNABLE_TO_FETCH_LOG_SIZE = 0x2051
ERR_MESSAGE_TYPE_ALREADY_EXISTS = 0x2052
ERR_UNKNOWN_MESSAGE_TYPE_OR_PART = 0x2053
ERR_MAX_RETRIES_CREATE_MESSAGE_TYPE = 0x2054
ERR_MAX_RETRIES_DELETE_MESSAGE_TYPE = 0x2055
ERR_MAX_RETRIES_INCREASE_CONCURRENCY = 0x2056
ERR_UNABLE_TO_CHANGE_RETENTION = 0x2057
ERR_UNABLE_DELETE_MESSAGES = 0x2058
ERR_UNABLE_TO_GET_MSG_COUNT = 0x2059
ERR_UNABLE_TO_RESET_OFFSET = 0x2060

# default
ERR_DEFAULT_ERROR_CODE = 0x2199


class MessageBusError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        if rc == ERR_DEFAULT_ERROR_CODE and args:
            error_codes = {errors.ERR_REQUEST_TIMED_OUT: ["_TIMED_OUT"],
                           ERR_MESSAGE_TYPE_ALREADY_EXISTS: ["TOPIC_ALREADY_EXISTS"],
                           errors.ERR_SERVICE_NOT_AVAILABLE: ["BROKER_NOT_AVAILABLE"],
                           ERR_LEADER_NOT_AVAILABLE: ["LEADER_NOT_AVAILABLE"],
                           errors.ERR_MESSAGE_TOO_LARGE: ["MESSAGE_TOO_LARGE"],
                           errors.ERR_UNSUPPORTED_VERSION: ["UNSUPPORTED_VERSION"],
                           errors.ERR_NETWORK_EXCEPTION: ["NETWORK_EXCEPTION"],
                           ERR_UNKNOWN_MESSAGE_TYPE_OR_PART: ["UNKNOWN_TOPIC_OR_PART"],
                           errors.ERR_INVALID_CONFIG: ["INVALID_CONFIG"],
                           errors.ERR_NOENTRY: ["NOENTRY"],
                           }
            for key, value in error_codes.items():
                return_code = [key for val in value if val in str(args)]
                if return_code:
                    self._rc = key
        self._desc = message % (args)

    @property
    def rc(self):
        return self._rc

    @property
    def desc(self):
        return self._desc

    def __str__(self):
        if self._rc == ERR_DEFAULT_ERROR_CODE:
            return self._desc
        return "error(%d): %s" % (self._rc, self._desc)
