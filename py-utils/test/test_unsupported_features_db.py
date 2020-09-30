#!/usr/bin/env python3

# CORTX-Utils: CORTX Python common library.
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
import os
import unittest

from cortx.utils.product_features.unsupported_features import UnsupportedFeaturesDB
from cortx.utils.schema.payload import Json

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_schema', 'test_unsupported_features_data.json')
TEST_DATA = Json(file_path).load()


class TestUnsupportedFeaturesDB(unittest.TestCase):
    _dm = UnsupportedFeaturesDB()
    _loop = asyncio.get_event_loop()

    def test_store_event(self):
        test_data = TEST_DATA.get("store_event", {})
        data = self._loop.run_until_complete(self._dm.store_unsupported_feature(
            **test_data.get('input')))
        self.assertEqual(data, test_data.get("output", ""))

    def test_get_event(self):
        test_data = TEST_DATA.get("get_event", {})
        data = self._loop.run_until_complete(
            self._dm.get_unsupported_features(**test_data.get('input')))
        print(data)
        self.assertDictEqual(data[0], test_data.get("output", ""))

    def test_support_event(self):
        test_data = TEST_DATA.get("support_event", {})
        data = self._loop.run_until_complete(self._dm.is_feature_supported(
            **test_data.get('input')))
        self.assertEqual(data, test_data.get("output", ""))

    def test_not_support_event(self):
        test_data = TEST_DATA.get("not_support_event", {})
        data = self._loop.run_until_complete(self._dm.is_feature_supported(
            **test_data.get('input')))
        self.assertEqual(data, test_data.get("output", ""))

    def test_multiple_store_event(self):
        test_data = TEST_DATA.get("multiple_store_events", {})
        data = self._loop.run_until_complete(
            self._dm.store_unsupported_features(**test_data.get('input')))
        self.assertEqual(data, test_data.get("output", ""))


if __name__ == '__main__':
    unittest.main()
