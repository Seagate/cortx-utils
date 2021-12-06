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

import os
import asyncio
import unittest
from cortx.utils.schema.payload import Json
from cortx.utils.ha.dm.repository.decisiondb import DecisionDB
dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_schema', 'test_decisiondb_data.json')
TEST_DATA = Json(file_path).load()

class TestDecisionDB(unittest.TestCase):
    _dm = DecisionDB()
    _loop = asyncio.get_event_loop()

    def test_store_event(self):
        test_data = TEST_DATA.get("store_event", {})
        data = self._loop.run_until_complete(self._dm.store_event(
            **test_data.get('input')))
        self.assertEqual(data, test_data.get("output", ""))

    def test_get_event(self):
        test_data = TEST_DATA.get("get_event", {})
        data = self._loop.run_until_complete(
            self._dm.get_event(**test_data.get('input')))
        for actual, expected in zip(data, test_data.get("output")):
            self.assertDictEqual(actual.to_primitive(), expected)

    def test_get_event_time(self):
        test_data = TEST_DATA.get("get_event_time", {})
        data = self._loop.run_until_complete(self._dm.get_event_time(
            **test_data.get('input')))
        for actual, expected in zip(data, test_data.get("output")):
            print(actual.to_primitive(), expected)
            actual_value = actual.to_primitive()
            self.assertDictEqual(actual_value , expected)

    def test_delete_event(self):
        test_data = TEST_DATA.get("delete_event", {})
        data = self._loop.run_until_complete(self._dm.get_event_time(
            **test_data.get('input')))
        self.assertEqual(data, test_data.get("output"))

    def test_get_entity_health(self):
        test_data = TEST_DATA.get("delete_event", {})
        data = self._loop.run_until_complete(self._dm.get_event_time(
            **test_data.get('input')))
        for actual, expected in zip(data, test_data.get("output")):
            print(actual.to_primitive(), expected)
            actual_value = actual.to_primitive()
            self.assertDictEqual(actual_value , expected)

if __name__ == '__main__':
    unittest.main()
