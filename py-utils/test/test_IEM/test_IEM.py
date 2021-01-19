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


sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from cortx.utils.schema.payload import Json
from cortx.utils.IEM_framework import IEM


dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'test_IEM_json.json')
sample_config = Json(file_path).load()

def setup_and_generate_sample_files():
    """ This function will generate all required types of file """
    with open(r'/tmp/file_IEM.json', 'w+') as file:
        json.dump(sample_config, file, indent=2)


class TestIEM(unittest.TestCase)
    """This class will test available API's in IEM"""
    def test_IEM_default_const(self):
        objectName=IEM()
        essage="Object is not type of IEM class"
        self.assertIsInstance(objectName,IEM,message)

    def test_IEM_params(self):
        result=IEM('A','H',0X001,0X100,0X2710,"crash",self.params)
        self.IEM.print_IEM()

    def test_populate(self):
        result1=self.populate('A','H',0X001,0X100,0X2710,"memory dump",salf.params)
        self.IEM.print_IEM()


if __name__ == '__main__':
    """
    Firstly create the file and load sample json into it.
    Start test
    """
    setup_and_generate_sample_files()
    unittest.main()
    
