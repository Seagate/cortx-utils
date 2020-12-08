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


class MessageConst():
    DEFAULT_MESSAGE_TYPE = 'default'
    MESSAGE_TYPE_LIST = ['default','Alert', 'Emergency', 'Notice', 'Performance', 'testing', 'testing1']

class MessageHeader():

    def __init__(self, m_type):
        self.msg_con_obj = MessageConfig()
        self.message_type = self.msg_con_obj.get_message_config(m_type)

    def create(self):
        pass
    def remove(self, type):
        pass
    def update(self, old, new):
        pass

class Message():

    def __init__(self, msg=None, message_type=None, m_format=None):
        self.payload = msg if m_format is None else self.format_message(msg, m_format)
        self.m_header = MessageHeader(message_type)
        self.m_formator = m_format

    def get_message_header(self): # make it protected
        # if type is not there.
        return self.m_header if self.m_header is not None else MessageHeader(MessageConst.DEFAULT_MESSAGE_TYPE)

    def get_message_type(self):
        if self.m_header is not None:
            message_type = self.m_header.message_type
        else:
            raise KeyError("Message type not exists")
        return message_type

    def get_message_attributes(self, attribute):
        pass

    def get_message(self):
        return self.payload if self.payload is not None else None

    def format_message(self, msg, m_format):
        return msg


class MessageConfig():

    def __init__(self):
        self.message_type = MessageConst().MESSAGE_TYPE_LIST

    def create(self, m_type):
        pass

    def get_message_config(self, m_type):
        if m_type in self.message_type:
            return m_type
        else:
            raise KeyError("Message configuration not found")

class MessageFormat():
    pass

