#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
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

import unittest
from consul import Consul
from cortx.utils.validator.v_service import ServiceV


class TestConsul(unittest.TestCase):
    def setUp(self) -> None:
        self.consul = Consul()

    def test_get(self):
        self.consul.kv.put("test_key", "test_value")
        result = self.consul.kv.get("test_key")
        self.assertEqual("test_value", result[1]["Value"].decode())
        self.consul.kv.delete("test_key")

    def test_put(self):
        result = self.consul.kv.put("test_key", "test_value")
        self.assertIs(result, True)
        self.consul.kv.delete("test_key")

    def test_delete(self):
        self.consul.kv.put("test_key", "test_value")
        result = self.consul.kv.delete("test_key")
        self.assertIs(result, True)

    def test_service_running(self):
        ServiceV().validate('isrunning', ["consul"])
