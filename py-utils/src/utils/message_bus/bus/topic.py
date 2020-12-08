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


class Topic():

    def __init__(self, topic_config):
        self.name = topic_config['name']
        self.replication_factor = topic_config['replication_factor']
        self.policy = topic_config['policy'] # Values to be set in bus.__init__ and It's class type.

    def create(self, topic_name, timeout_ms=None, validate_only=False):
        return self.bus_handle.create_topic(topic_name, timeout_ms, validate_only)

    def get_topic(self,message):
        return self.bus_handle.get_topic(message)

    def get_all_topics(self):
        return self.bus_handle.get_all_topics()