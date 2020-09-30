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

from cortx.utils.errors import BaseError
from cortx.utils.log import Log

OPERATION_SUCCESSFUL = 0x0000
CONNECTION_ERROR = 0x1001
INTERNAL_ERROR = 0x1002
INVALID_CONFIG = 0x1003
SEND_ERROR = 0x1004
MSG_FETCH_ERROR = 0x1005
NO_MSG_ERROR = 0x1006
COMMIT_ERROR = 0x1007
DISCONNECT_ERROR = 0x1008


class MessagebusError(BaseError):

    """Parent class for the Messagebus error classes."""
    def __init__(self, rc=0, desc=None, message_id=None, message_args=None):
        super().__init__(
            rc=rc, desc=desc, message_id=message_id, message_args=message_args)
        Log.error(f"{self._rc}:{self._desc}:{self._message_id}:{self._message_args}")


class InvalidConfigError(MessagebusError):

    """This error will be raised when an invalid config is received."""
    _err = INVALID_CONFIG
    _desc = "MessagebusError: Invalid config received."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            INVALID_CONFIG, _desc, message_id, message_args)


class OperationSuccessful:

    """This will be raised when an operation is successfull."""
    def __init__(self, desc):
        self._rc = OPERATION_SUCCESSFUL
        self._desc = desc

    def msg(self):
        return f"MessagebusSuccess({self._rc}) : {self._desc}"


class ConnectionEstError(MessagebusError):

    """This error will be raised when connection could not be established."""
    _err = CONNECTION_ERROR
    _desc = "MessagebusError: Connection establishment failed."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            CONNECTION_ERROR, _desc, message_id, message_args)


class SendError(MessagebusError):

    """This error will be raised when message sending is failed."""
    _err = SEND_ERROR
    _desc = "MessagebusError: Message sending failed."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            SEND_ERROR, _desc, message_id, message_args)


class NoMsgError(MessagebusError):

    """This error will be raised when no message is fetch."""
    _err = NO_MSG_ERROR
    _desc = "MessagebusError: No Message to deliver."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            NO_MSG_ERROR, _desc, message_id, message_args)


class MsgFetchError(MessagebusError):

    """This error will be raised when no message is fetch."""
    _err = MSG_FETCH_ERROR
    _desc = "MessagebusError: Error occurred in fetching message."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            MSG_FETCH_ERROR, _desc, message_id, message_args)


class DisconnectError(MessagebusError):

    """This error will be raised when disconnecting consumer operation failed."""
    _err = DISCONNECT_ERROR
    _desc = "MessagebusError: Error occurred in disconnecting."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            DISCONNECT_ERROR, _desc, message_id, message_args)


class CommitError(MessagebusError):

    """This error will be raised when receive commit is failed."""
    _err = COMMIT_ERROR
    _desc = "MessagebusError: Error occurred in receive commit."

    def __init__(self, _desc=None, message_id=None, message_args=None):
        super().__init__(
            COMMIT_ERROR, _desc, message_id, message_args)
