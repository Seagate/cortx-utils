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

import os
import unittest
import yaml

from cortx.utils.conf_store import MappedConf, Conf

dir_path = os.path.dirname(os.path.realpath(__file__))

def create_file(file, data=""):
    """Creates temporary file."""
    try:
        with open(file, 'w+') as temp_file:
            temp_file.write(data)
    except OSError as e:
        print(e)

def delete_file(file):
    """Deletes temporary files."""
    try:
        if os.path.exists(file):
            os.remove(file)
    except OSError as e:
        print(e)

class TestMappedConf(unittest.TestCase):
    """Test MappedConf."""

    def test_mapped_conf_add_num_keys(self):
        """Test if add_num_keys adds num_xx keys for xx list in the given config."""
        data = {
            'a' : '1',
            'b' : ['2', {'3': ['5', '6']}, '4']
        }
        sample_file = f"{dir_path}/sample_conf.yaml"
        create_file(sample_file, yaml.dump(data))
        conf_url = f"yaml:///{sample_file}"
        cortx_conf = MappedConf(conf_url)
        cortx_conf.add_num_keys()
        test_index = 'test_index1'
        Conf.load(test_index, conf_url)
        # Test before saving
        self.assertIsNone(Conf.get(test_index, 'num_b'), "num_b key is added without even saving to conf")
        self.assertIsNone(Conf.get(test_index, 'b>num_3'), "num_b key is added without even saving to conf")
        # Test after saving
        test_index = 'test_index2'
        conf_id = cortx_conf._conf_idx
        Conf.save(conf_id)
        Conf.load(test_index, conf_url)
        self.assertEqual(Conf.get(test_index, 'num_b'), 3)
        self.assertEqual(Conf.get(test_index, 'b[1]>num_3'), 2)
        delete_file(sample_file)

if __name__ == '__main__':
    unittest.main()
