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

import inspect

OPERATION_SUCESSFUL = 0x0000
INTERNAL_ERROR = 0x1005
ERR_OP_FAILED = 0x1100
ERR_INVALID_CLIENT_TYPE = 0x1501
ERR_INVALID_SERVICE_NAME = 0x1502
ERR_SERVICE_UNAVAILABLE = 0x1503
ERR_SERVICE_NOT_INITIALIZED = 0x1504
ERR_NOT_INITIALIZED = 0x1505
ERR_INVALID_MESSAGE_TYPE = 0x1506


class UtilsError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    @property
    def rc(self):
        return self._rc

    @property
    def desc(self):
        return self._desc

    def __str__(self):
        if self._rc == 0:
            return self._desc
        return "error(%d): %s" %(self._rc, self._desc)


class BaseError(Exception):
    """ Parent class for the cli error classes """

    _rc = OPERATION_SUCESSFUL
    _desc = 'Operation Successful'
    _caller = ''

    def __init__(self, rc=0, desc=None, message_id=None, message_args=None):
        super(BaseError, self).__init__()
        self._caller = inspect.stack()[1][3]
        if rc is not None:
            self._rc = str(rc)
        self._desc = desc or self._desc
        self._message_id = message_id
        self._message_args = message_args

    def message_id(self):
        return self._message_id

    def message_args(self):
        return self._message_args

    def rc(self):
        return self._rc

    def error(self):
        return self._desc

    def caller(self):
        return self._caller

    def __str__(self):
        return "error(%s): %s" % (self._rc, self._desc)


class InternalError(BaseError):
    """
    This error is raised by CLI for all unknown internal errors
    """

    def __init__(self, desc=None, message_id=None, message_args=None):
        super(InternalError, self).__init__(
              INTERNAL_ERROR, 'Internal error: %s' % desc,
              message_id, message_args)

class DataAccessError(InternalError):

    """Base Data Access Error"""


class DataAccessExternalError(DataAccessError):

    """Internal DB errors which happen outside of db framework"""


class DataAccessInternalError(DataAccessError):

    """Errors regarding db framework part of Data Access implementation"""


class MalformedQueryError(DataAccessError):

    """Malformed Query or Filter error"""


class MalformedConfigurationError(DataAccessError):

    """Error in configuration of data bases or storages or db drivers"""


class StorageNotFoundError(DataAccessError):

    """Model object is not associated with any storage"""


class AmqpConnectionError(Exception):

    """ Amqp connection problems """


class TestFailed(Exception):
    """
    Errors related to test execution
    """
    def __init__(self, desc):
        self.desc = '[%s] %s' %(inspect.stack()[1][3], desc)
        super(TestFailed, self).__init__(desc)
