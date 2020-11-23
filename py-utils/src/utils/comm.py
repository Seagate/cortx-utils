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

from abc import ABCMeta, abstractmethod

class Channel(metaclass=ABCMeta):

    """Abstract class to represent a comm channel to a node"""

    @abstractmethod
    def init(self):
        raise Exception('init not implemented in Channel class')

    @abstractmethod
    def connect(self):
        raise Exception('connect not implemented in Channel class')

    @abstractmethod
    def disconnect(self):
        raise Exception('disconnect not implemented in Channel class')

    @abstractmethod
    def send(self, message):
        raise Exception('send not implemented in Channel class')

    @abstractmethod
    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented in Channel class')

    @abstractmethod
    def recv(self, message=None):
        raise Exception('recv not implemented in Channel class')

    @abstractmethod
    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented in Channel class')

    @abstractmethod
    def acknowledge(self, delivery_tag=None):
        raise Exception('acknowledge not implemented for Channel class')


class Comm(metaclass=ABCMeta):

    """Abstract class to represent a comm channel"""

    @abstractmethod
    def init(self):
        raise Exception('init not implemented in Comm class')

    @abstractmethod
    def connect(self):
        raise Exception('connect not implemented in Comm class')

    @abstractmethod
    def disconnect(self):
        raise Exception('disconnect not implemented in Comm class')

    @abstractmethod
    def send(self, message, **kwargs):
        raise Exception('send not implemented in Comm class')

    @abstractmethod
    def send_message_list(self, message: list, **kwargs):
        raise Exception('send_message_list not implemented in Comm class')

    @abstractmethod
    def recv(self, callback_fn=None, message=None, **kwargs):
        raise Exception('recv not implemented in Comm class')

    @abstractmethod
    def acknowledge(self):
        raise Exception('acknowledge not implemented in Comm class')
