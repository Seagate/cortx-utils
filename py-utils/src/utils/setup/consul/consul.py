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


import time
import traceback
import os
import json
import re
import pathlib
import shutil

from jinja2 import FileSystemLoader

from cortx.utils.conf_store import Conf
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.validator.error import VError
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from jinja2.environment import Environment
try:
    from cortx.utils.test.consul import TestConsul
except ImportError:
    pass 


class ConsulSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" %(self._rc, self._desc,
            traceback.format_exc())

    @property
    def rc(self):
        return self._rc


class Consul:
    """ Represents Consul and Performs setup related actions """
    index = "consul"

    def __init__(self, conf_url):
        Conf.load(self.index, conf_url)

    def validate_post_install(self):
        """ Perform validtions. Raises exceptions if validation fails """
        PkgV().validate('rpms', ['consul-1.9.1-1'])
    
    def validate_config(self, server_node_fqdns):
        max_retry = 3
        for i in range(max_retry):
            try:
                NetworkV().validate(
                    "connectivity", server_node_fqdns)
                break
            except VError:
                if i == (max_retry-1):
                    raise
                time.sleep(0.5)

    def post_install(self):
        """ Performs post install operations. Raises exception on error """

        config_path = Conf.get(self.index, "cortx>software>consul>config_path", "/etc/consul.d")
        data_path = Conf.get(self.index, "cortx>software>consul>data_path", "/opt/consul")
        os.makedirs(config_path, exist_ok=True)     
        os.makedirs(data_path, exist_ok=True)
        content = ""
        with open("/usr/lib/systemd/system/consul.service") as f:
            content = f.read()
        with open("/usr/lib/systemd/system/consul.service", "w") as f:
            content = re.sub("config-dir=.*",
                   f"config-dir={config_path}",
                   content)
            content = re.sub("ConditionFileNotEmpty=.*",
                   f"ConditionFileNotEmpty={config_path}/consul.hcl",
                   content)
            f.write(content)

        command = "systemd-analyze verify consul.service"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            ConsulSetupError(returncode, "Consul Setup systemd service file validation failed with error: %s" % err)

        command = "systemctl daemon-reload"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            ConsulSetupError(returncode, "Consul Setup systemd daemon-reload failed with error: %s" % err)
        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """

        bind_addr = Conf.get(self.index, f"server_node>{Conf.machine_id}>network>data>private_interfaces[0]")
        config_path = Conf.get(self.index, "cortx>software>consul>config_path", "/etc/consul.d")
        data_path = Conf.get(self.index, "cortx>software>consul>data_path", "/opt/consul")
        self.cluster_id = Conf.get(self.index, f"server_node>{Conf.machine_id}>cluster_id")
        server_node_fqdns = []
        storage_sets = Conf.get(self.index, f"cluster>{self.cluster_id}>storage_set")
        for storage_set in storage_sets: 
            for server_node in storage_set["server_nodes"]:
                if self.run_as_server(server_node) and server_node != Conf.machine_id:
                    server_node_fqdns.append(
                        Conf.get(self.index, f"server_node>{server_node}>network>data>private_fqdn")
                    )

        server = self.run_as_server(Conf.machine_id)
        env = Environment(loader=FileSystemLoader("/opt/seagate/cortx/utils/conf"))
        template = env.get_template('consul.hcl.tmpl')
        template.stream(bind_addr=bind_addr,
                        data_dir=data_path,
                        retry_join=json.dumps(server_node_fqdns),
                        server=str(server).lower(),
                        bootstrap_expect=2).dump(f"{config_path}/consul.hcl")
        command = f"consul validate {config_path}/consul.hcl"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            ConsulSetupError(returncode, 
                            "Consul Setup config file %s validation failed with error :%s"
                            %(f"{config_path}/consul.hcl", err))
        command = f"chown -R consul:consul {config_path} {data_path}"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            ConsulSetupError(returncode, 
                            "Consul Setup changing ownership failed for %s %s with error: %s"
                            %(config_path, data_path, err))
        return 0

    def run_as_server(self, server_node):
        storage_set_count = int(Conf.get(self.index, f"cluster>{self.cluster_id}>site>storage_set_count"))

        node_id = int(Conf.get(self.index, f"server_node>{server_node}>node_id"))
        if storage_set_count < 5:
            if node_id < 4:
                return True
        elif storage_set_count == 6:
            if node_id < 6:
                return True
        elif storage_set_count == 12:
            if node_id < 8:
                return True
        return False


    def test(self, plan):
        """ Perform configuration testing. Raises exception on error """

        if "TestConsul" in globals():
            test_consul = TestConsul()
            test_consul.put()
            test_consul.get()
            test_consul.delete()
        else:
            print("Install cortx-py-utils-test to run test")
        return 0

    def reset(self):
        """ Performs Configuraiton reset. Raises exception on error """

        command = f"consul kv delete --recurse"
        SimpleProcess(command).run()
        return 0

    def cleanup(self, pre_factory=False):
        self.reset()
        content = ""
        with open("/usr/lib/systemd/system/consul.service") as f:
            content = f.read()

        with open("/usr/lib/systemd/system/consul.service", "w") as f:
            content = re.sub("config-dir=.*",
                   f"config-dir=/etc/consul.d",
                   content)
            content = re.sub("ConditionFileNotEmpty=.*",
                   f"ConditionFileNotEmpty=/etc/consul.d/consul.hcl",
                   content)
            f.write(content)

        command = "systemctl daemon-reload"
        _, err, returncode = SimpleProcess(command).run()
        if returncode != 0:
            ConsulSetupError(returncode, "Consul Setup systemd daemon-reload failed with error: %s" % err)
        shutil.move(f"{pathlib.Path(__file__).parent}/templates/consul.hcf.default",
         "/etc/consul.d/consul.hcl")
    
        if pre_factory:
            config_path = Conf.get(self.index, "cortx>software>consul>config_path")
            data_path = Conf.get(self.index, "cortx>software>consul>data_path", "/opt/consul")
            shutil.rmtree(config_path, ignore_errors=True)     
            shutil.rmtree(data_path, ignore_errors=True)
            if not config_path:
                os.makedirs(config_path, exist_ok=True)
            os.makedirs(config_path, exist_ok=True)
            shutil.move(f"{pathlib.Path(__file__).parent}/templates/consul.hcf.default",
                        "/etc/consul.d/consul.hcl")
            command = f"chown -R consul:consul {config_path}"
            _, err, returncode = SimpleProcess(command).run()
            if returncode != 0:
                ConsulSetupError(returncode, 
                                "Consul Setup changing ownership failed for %s %s with error: %s"
                                %(config_path, data_path, err))
            return 0
