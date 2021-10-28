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
import unittest
from unittest.mock import MagicMock
import asyncio

from cortx.utils.ha.dm.decision_maker import DecisionMaker
from cortx.utils.schema.payload import Json, JsonMessage
from cortx.utils.ha.dm.repository.decisiondb import DecisionDB

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_alert.json')
rules_schema_path = os.path.join(dir_path, 'rules_engine_schema.json')

class TestDecisionMaker(unittest.TestCase):
    """Module to test DecisionMaker class"""

    res_to_entity_mapping = {
        "enclosure": ("enclosure", "connectivity"),
        "enclosure:fru:controller": ("enclosure", "controller")
        }

    mock_decisiondb = DecisionDB()
    _dec_maker = DecisionMaker(decisiondb=mock_decisiondb)
    json_alert_data = Json(file_path).load()
    rules_data = Json(rules_schema_path).load()
    _loop = asyncio.get_event_loop()

    def test_handle_alert(self):
        """tests handle_alert functio of DecisionMaker class"""

        assert self.json_alert_data is not None
        self.assertTrue(isinstance(self.json_alert_data, dict))
        self._loop.run_until_complete(self._dec_maker.handle_alert(self.json_alert_data))
        res_type = self.json_alert_data["message"]["sensor_response_type"]["info"]["resource_type"]
        res_id = self.json_alert_data["message"]["sensor_response_type"]["info"]["resource_id"]
        host_id = self.json_alert_data["message"]["sensor_response_type"]["host_id"]
        event_time = self.json_alert_data["message"]["sensor_response_type"]["info"]["event_time"]
        alert_type = self.json_alert_data["message"]["sensor_response_type"]["alert_type"]
        severity = self.json_alert_data["message"]["sensor_response_type"]["severity"]
        tuple_val = self.res_to_entity_mapping[res_type]
        entity, component = tuple_val[0], tuple_val[1]
        if entity == "enclosure":
            entity_id = '0'
        else:
            entity_id = host_id
        if res_type == "enclosure":
            component_id = host_id
        else:
            component_id = res_id

        action = ''
        res_type_data = self.rules_data[res_type]
        if res_type_data is not None:
            for item in res_type_data:
                if alert_type == item["alert_type"] and \
                    severity == item["severity"]:
                    action = item["action"]

        self.mock_decisiondb.store_event.assert_called_with(entity, entity_id, \
            component, component_id, event_time, action)

if __name__ == '__main__':
    unittest.main()
