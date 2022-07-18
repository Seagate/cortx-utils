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
from urllib.parse import urlparse
from consul import Consul

from cortx.utils.conf_store import Conf
from cortx.utils.validator.v_service import ServiceV


class TestConsul(unittest.TestCase):

# GConf url is supplied by CORTX provisioner during component mini-provisioning,
# which is not available for tests here, so hardcoded Gconf address.
# Added this as a class constant. This will enable to run this module independently.

    GCONF = "consul://cortx-consul-server:8500/conf"

    @classmethod
    def setUpClass(cls) -> None:
        Conf.load("index", cls.GCONF, skip_reload=True)
        num_consul_endpoints = Conf.get("index", f'cortx>external>consul>num_endpoints')
        for i in range(int(num_consul_endpoints)):
            endpoint = Conf.get("index", f'cortx>external>consul>endpoints[{i}]')
            parsed_url = urlparse(endpoint)
            if parsed_url.scheme == 'http':
                consul_host = parsed_url.hostname
                consul_port = parsed_url.port
                break
        cls.consul = Consul(host=consul_host, port=consul_port)

    def test_get(self):
        self.consul.kv.put(f"test/{Conf.machine_id}", 'spam')
        result = self.consul.kv.get(f"test/{Conf.machine_id}")
        self.assertEqual('spam', result[1]['Value'].decode())
        self.consul.kv.delete(f"test/{Conf.machine_id}")

    def test_put(self):
        result = self.consul.kv.put(f"test/{Conf.machine_id}", 'spam')
        self.assertIs(result, True)
        self.consul.kv.delete(f"test/{Conf.machine_id}")

    def test_delete(self):
        self.consul.kv.put(f"test/{Conf.machine_id}", 'spam')
        result = self.consul.kv.delete(f"test/{Conf.machine_id}")
        self.assertIs(result, True)

    def test_service_running(self):
        ServiceV().validate('isrunning', ['consul'])


if __name__ == '__main__':
    unittest.main()
