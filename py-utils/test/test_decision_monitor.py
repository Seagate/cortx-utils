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

import asyncio
import datetime
import os
import unittest

from cortx.utils.ha.dm.decision_monitor import DecisionMonitor
from cortx.utils.ha.dm.repository.decisiondb import DecisionDB
from cortx.utils.schema.payload import Json

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_schema', 'test_decision_monitor_data.json')
TEST_DATA = Json(file_path).load()


def _generate_data():
    d = DecisionDB()
    for index, each_input in enumerate(TEST_DATA.get("input", [])):
        each_input["alert_time"] = str(
            datetime.datetime.now() + datetime.timedelta(hours=index))
        d.store_event(**each_input)


class TestDecisionMonitor(unittest.TestCase):
    _dm = DecisionMonitor()
    _dm._resource_file = TEST_DATA.get("test_file")
    _loop = asyncio.get_event_loop()
    _generate_data()

    def test_resource_group(self):
        data = self._loop.run_until_complete(
            self._dm.get_resource_group_status("io_c1"))
        self.assertEqual("resolved", data)

    def test_acknowledge_resource_group(self):
        data = self._loop.run_until_complete(
            self._dm.acknowledge_resource_group("io_c1"))
        self.assertIsNone(data)


if __name__ == '__main__':
    unittest.main()
