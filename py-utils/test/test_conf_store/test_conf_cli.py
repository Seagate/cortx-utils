#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import os
import sys
import unittest
from cortx.utils.process import SimpleProcess

base_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(base_path)
from cortx.utils.schema.payload import Json

conf = os.path.join(base_path, "src", "utils", "conf_store", "conf_cli.py")

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_conf_sample_json.json')
sample_config = Json(file_path).load()

def setup_and_generate_sample_files():
    """ This function will generate all required types of file """
    with open(r'/tmp/file1.json', 'w+') as file:
        json.dump(sample_config, file, indent=2)

def run(cmd):
    proc = SimpleProcess(cmd)
    out, err, rc = proc.run()
    return out, err, rc

class TestConfCli(unittest.TestCase):
    """Test case will test available API's of ConfStore"""

    def test_conf_cli_get(self):
        """ Test by retrieving a value using get api """
        cmd = f"{conf} json:///tmp/file1.json get 'bridge>name'"
        out, err, rc = run(cmd)

        print("@@@ test_conf_cli_get 'bridge>name' ", out)
        out = json.loads(out)
        self.assertEqual(out, ["Homebridge"])

    def test_conf_cli_set(self):
        """ Test by setting a value into given key position """
        cmd = f"{conf} json:///tmp/file1.json set 'bridge>cli_name=client'"
        out, err, rc = run(cmd)

        cmd = f"{conf} json:///tmp/file1.json get 'bridge>cli_name'"
        out, err, rc = run(cmd)

        print("@@@ test_conf_cli_set ", out)
        out = json.loads(out)
        self.assertEqual(out, ["client"])

    def test_conf_cli_get_list(self):
        """ Test by retrieving list of values for given keys seperated by ;"""
        cmd = f"{conf} json:///tmp/file1.json get bridge>name;bridge>lte_type[0]>name"
        out, err, rc = run(cmd)

        print("@@@ test_conf_cli_get_list ", out)
        out = json.loads(out)
        self.assertListEqual(out, ['Homebridge', '3g'])

    def test_conf_cli_set_list(self):
        """
        Test by setting list of k,v seperated by ';' semicolon into conf
        """
        cmd = f"{conf} json:///tmp/file1.json set 'bridge>cli_name=client;bridge>has_internet=no'"
        out, err, rc = run(cmd)

        cmd = f"{conf} json:///tmp/file1.json get 'bridge>cli_name;bridge>has_internet'"
        out, err, rc = run(cmd)

        print("@@@ test_conf_cli_set_list ", out)

        out = json.loads(out)
        self.assertListEqual(out, ['client', 'no'])

    def test_conf_cli_delete(self):
        """ Test by deleting a value from the conf """
        cmd = f"{conf} json:///tmp/file1.json delete 'bridge>port'"
        out, err, rc = run(cmd)

        cmd = f"{conf} json:///tmp/file1.json get 'bridge>port'"
        out, err, rc = run(cmd)

        print("@@@ test_conf_cli_delete ", out)
        self.assertEqual(len(out.strip()), 0)


if __name__ == '__main__':

    # create the file and load sample json into it. Start test
    setup_and_generate_sample_files()
    unittest.main()
