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


class BusClient():
    def __init__(self, bus_handle, role, consumer_group=None, message_type=None, auto_offset_reset=None):
        self.role = role
        self.bus_handle = bus_handle
        self.message_type = message_type
        self.consumer_group = consumer_group
        self.bus_client = self.bus_handle.create(self.role, self.consumer_group, self.message_type, auto_offset_reset)

    def send(self, message):
        self.bus_handle.send(self.bus_client, message, self.message_type)

    def receive(self):
        return self.bus_handle.receive()

    def create(self):
        self.bus_handle.create(self.role)