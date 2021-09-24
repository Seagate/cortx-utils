#!/bin/env python3

# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import errno
import time
import traceback
import os
import json
import re
import shutil
import unittest

from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.validator.error import VError
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_service import ServiceV
from cortx.utils.service.service_handler import Service, ServiceError


class ConsulSetupError(Exception):

    """ Generic Exception with error code and output """
    def __init__(self, rc, message, *args):
        """Initialize class."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Implement custom printable string representation."""
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" % (self._rc, self._desc,
                                        traceback.format_exc())

    @property
    def rc(self):
        return self._rc


class Consul:

    """Represents Consul and Performs setup related actions."""
    index = "consul"

    def __init__(self, conf_url):
        """Initialize class."""
        Conf.load(self.index, conf_url)

    def validate(self, stage):
        if stage == "post_install":
            PkgV().validate('rpms', ['consul'])
        elif stage == "config":
            keys = [
                f"server_node>{Conf.machine_id}>network>data>private_interfaces",
                f"server_node>{Conf.machine_id}>network>data>private_fqdn",
                "cortx>software>consul>config_path",
                "cortx>software>consul>data_path",
            ]
            for key in keys:
                value = Conf.get(self.index, key)
                if not value:
                    raise ConfError(
                        errno.EINVAL,
                        "Consul Setup config validation falied. %s key not found",
                        key)
            max_retry = 3
            server_node_fqdns = [
                Conf.get(
                    self.index,
                    f"server_node>{machine_id}>network>data>private_fqdn")
                for machine_id in Conf.get(self.index, "server_node").keys()
            ]
            for i in range(max_retry):
                try:
                    NetworkV().validate("connectivity", server_node_fqdns)
                    break
                except VError:
                    if i == (max_retry - 1):
                        raise
                    time.sleep(0.5)
        elif stage == "cleanup":
            keys = [
                "cortx>software>consul>config_path",
                "cortx>software>consul>data_path",
            ]
            for key in keys:
                value = Conf.get(self.index, key)
                if not value:
                    raise ConfError(
                        errno.EINVAL,
                        "Consul Setup config validation falied. %s key not found",
                        key)

    def post_install(self):
        """Performs post install operations. Raises exception on error."""
        pass

    def prepare(self):
        """Performs prepare operations. Raises exception on error."""
        pass

    def init(self):
        """Perform initialization. Raises exception on error."""
        max_retry = 3
        for i in range(max_retry):
            try:
                Service("consul.service").start()
                ServiceV().validate('isrunning', ["consul"])
                break
            except (VError, ServiceError):
                if i == (max_retry - 1):
                    raise
                time.sleep(0.5)

    def config(self):
        """Performs configurations. Raises exception on error."""
        config_path = Conf.get(self.index, "cortx>software>consul>config_path",
                               "/etc/consul.d")
        data_path = Conf.get(self.index, "cortx>software>consul>data_path",
                             "/opt/consul")
        os.makedirs(config_path, exist_ok=True)
        os.makedirs(data_path, exist_ok=True)
        content = ""
        with open("/usr/lib/systemd/system/consul.service", "r+") as f:
            content = f.read()
            content = re.sub("config-dir=.*", f"config-dir={config_path}",
                             content)
            content = re.sub(
                "ConditionFileNotEmpty=.*",
                f"ConditionFileNotEmpty={config_path}/consul.hcl", content)
            content = re.sub(
                "User=.*", "User=root",
                content
            )
            content = re.sub(
                "Group=.*", "Group=root",
                content
            )
            f.seek(0)
            f.truncate()
            f.write(content)

        command = "systemd-analyze verify consul.service"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(
                returncode,
                "Consul Setup systemd service file validation failed with error: %s",
                err)

        command = "systemctl daemon-reload"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(
                returncode,
                "Consul Setup systemd daemon-reload failed with error: %s",
                err)

        bind_addr = Conf.get(
            self.index,
            f"server_node>{Conf.machine_id}>network>data>private_interfaces[0]"
        )
        # server_node_fqdn have fqdn of nodes on which consul will run in server
        # mode. It is used for retry-join config
        server_node_fqdns = []
        bootstrap_expect = 0
        is_server_node = False
        for machine_id in Conf.get(self.index, "server_node").keys():
            if "consul_server" in Conf.get(self.index,
                                           f"server_node>{machine_id}>roles",
                                           []):
                bootstrap_expect += 1
                if machine_id != Conf.machine_id:
                    server_node_fqdns.append(
                        Conf.get(
                            self.index,
                            f"server_node>{machine_id}>network>data>private_fqdn"
                        ))
                else:
                    is_server_node = True

        with open(f"{config_path}/consul.hcl", "w") as f:
            with open("/opt/seagate/cortx/utils/conf/consul.hcl.tmpl") as t:
                content = t.read()
                content = content.replace("BIND_ADDR", bind_addr)
                content = content.replace("DATA_DIR", data_path)
                content = content.replace("SERVER", str(is_server_node).lower())
                content = content.replace("BOOTSTRAP_EXPECT", str(bootstrap_expect))
                content = content.replace("RETRY_JOIN", json.dumps(server_node_fqdns))
                f.write(content)

        command = f"consul validate {config_path}/consul.hcl"

        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(
                returncode,
                "Consul Setup config file %s validation failed with error :%s",
                f"{config_path}/consul.hcl", err)
        command = f"chown -R root:root {config_path} {data_path}"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(
                returncode,
                "Consul Setup changing ownership failed for %s %s with error: %s",
                config_path, data_path, err)

    def get_test_module(self):
        try:
            from cortx.utils.test.consul.consul import TestConsul
        except ImportError:

            class TestConsul(unittest.TestCase):
                def runTest(self):
                    print("Install cortx-py-utils-test to run test")

        return TestConsul

    def test(self):
        """Perform configuration testing. Raises exception on error."""
        unittest.TextTestRunner().run(
            unittest.TestLoader().loadTestsFromTestCase(
                self.get_test_module()))

    def reset(self):
        """Performs Configuraiton reset. Raises exception on error."""
        command = "consul kv delete --recurse"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(returncode,
                                   "Consul data reset failed with error: %s",
                                   err)

    def cleanup(self, pre_factory=False):
        try:
            Service("consul.service").stop()
        except ServiceError:
            pass

        content = ""
        with open("/usr/lib/systemd/system/consul.service", "r+") as f:
            content = f.read()
            content = re.sub("config-dir=.*", "config-dir=/etc/consul.d",
                             content)
            content = re.sub("ConditionFileNotEmpty=.*",
                             "ConditionFileNotEmpty=/etc/consul.d/consul.hcl",
                             content)
            content = re.sub(
                "User=.*", "User=consul",
                content
            )
            content = re.sub(
                "Group=.*", "Group=consul",
                content
            )
            f.seek(0)
            f.truncate()
            f.write(content)

        command = "systemctl daemon-reload"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(
                returncode,
                "Consul Setup systemd daemon-reload failed with error: %s" %
                err)

        config_path = Conf.get(self.index, "cortx>software>consul>config_path",
                               "/etc/consul.d")
        shutil.rmtree(config_path, ignore_errors=True)
        os.makedirs("/etc/consul.d", exist_ok=True)
        shutil.copy("/opt/seagate/cortx/utils/conf/consul.hcf.default",
                    "/etc/consul.d/consul.hcl")
        command = "chown -R consul:consul /etc/consul.d"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            raise ConsulSetupError(
                returncode,
                "Consul Setup changing ownership failed for %s with error: %s",
                config_path, err)
        data_path = Conf.get(self.index, "cortx>software>consul>data_path",
                             "/opt/consul/")
        shutil.rmtree(data_path, ignore_errors=True)

        if pre_factory:
            pass

    def preupgrade(self):
        pass

    def postupgrade(self):
        pass
