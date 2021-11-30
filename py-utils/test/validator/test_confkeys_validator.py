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

import json
import unittest
import os

from cortx.utils.conf_store import Conf
from cortx.utils.validator.v_confkeys import ConfKeysV

json_test_data ={
"bridge": {
"name": "Homebridge",
"username": "CC:22:3D:E3:CE:30",
"manufacturer": "homebridge.io",
"model": "homebridge",
"pin": "031-45-154",
"port": 51826,
"lte_type": [{"name": "3g"}, {"name": "4g"}]
}
}

index="test_conf_idx"
test_backend_file="/tmp/testfile.json"
test_backend_url=f"json://{test_backend_file}"

def generate_config():
    try:
        with open(f"{test_backend_file}", 'w', encoding='utf-8') as f:
            json.dump(json_test_data, f, indent=4)
    except Exception as e:
        raise Exception(f"Unexpected exception in generate_config(): {e}")


class TestConfStore(unittest.TestCase):
    """Test case will test available API's of v_confkeys"""

    @classmethod
    def setUpClass(cls):
        generate_config()

    def test_confkeys_exist(self):
        """Check if keys exist."""
        try:
            Conf.load(index, test_backend_url)
            ConfKeysV().validate('exists', index, ['bridge', 'bridge>name'])
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_confkeys_not_exist(self):
        """Check if keys not exist."""
        try:
            ConfKeysV().validate('exists', index, ['bridge', 'bridge>port_no'])
        except Exception as e:
            if "key missing" not in f"{e}":
                raise Exception(f"Unexpected exception: {e}")
            return
        self.fail("Unexpected test pass, this key should not be found.")

    @classmethod
    def tearDownClass(cls):
        os.remove(test_backend_file)


if __name__ == '__main__':
    unittest.main()
