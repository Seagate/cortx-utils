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

import os
import errno
import shutil
import socket
import traceback
import unittest

from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.service.service_handler import Service
from cortx.utils.validator.error import VError
from cortx.utils.service.service_handler import ServiceError


class ElasticsearchSetupError(Exception):
    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Return error msg."""
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" % (
            self._rc, self._desc, traceback.format_exc())

    def rc(self):
        return self._rc


class Elasticsearch:
    """Represents Elasticsearch and Performs setup related actions."""

    index = "Elasticsearch"

    elasticsearch_cluster_name = "elasticsearch_cluster"
    http_port = 9200
    elasticsearch_config_path = "/etc/elasticsearch/elasticsearch.yml"
    log_path = "/var/log/elasticsearch"
    data_path = "/var/lib/elasticsearch"
    elasticsearch_file_path = "/opt/seagate/cortx/utils/conf/elasticsearch"
    opendistro_security_plugin = "/usr/share/elasticsearch/plugins/opendistro_security"
    rsyslog_conf = "/etc/rsyslog.conf"

    Log.init(
        'ElasticsearchProvisioning',
        '/var/log/cortx/utils/elasticsearch',
        level='DEBUG')

    def __init__(self, conf_url):
        """Initialize config."""
        Conf.load(self.index, conf_url)

    def validate(self, phase: str):
        """
        Perform validations.

        Raises exceptions if validation fails.
        """
        if phase == "post_install":
            # Perform python pkg validations.
            pip3_packages = {
                "elasticsearch": "7.12.0",
                "elasticsearch-dsl": "7.3.0"
            }
            # Validate pre-requisites software packages.
            rpm_packages = {
                "opendistroforelasticsearch": "1.12.0"
            }
            try:
                PkgV().validate_pip3_pkgs(
                    host=socket.getfqdn(),
                    pkgs=pip3_packages, skip_version_check=False)
                PkgV().validate_rpm_pkgs(
                    host=socket.getfqdn(),
                    pkgs=rpm_packages, skip_version_check=False)
                PkgV().validate("rpms", ["java-1.8.0-openjdk-headless"])
            except VError as e:
                msg = f"Validation failed for {phase} phase with error {e}."
                Log.error(msg)
                raise

        elif phase == "config":
            if os.path.exists(self.opendistro_security_plugin):
                msg = ('Opendistro_security plugin path '
                       f'{self.opendistro_security_plugin} is not deleted.')
                Log.error(msg)
                raise Exception(msg)

        elif phase == "init":
            Log.info("No validation needed for init phase.")
        elif phase == "prepare":
            Log.info("No validation needed for prepare phase.")
        elif phase == "cleanup":
            Log.info("No validation needed for cleanup phase.")
        elif phase == "pre_upgrade":
            Log.info("No validation needed for pre_upgrade phase.")
        elif phase == "post_upgrade":
            Log.info("No validation needed for post_upgrade phase.")

        return 0

    def post_install(self):
        """
        Performs post install operations.

        Raises exception on error
        """
        try:
            # Remove opendistro_security plugins.
            Elasticsearch.delete_path(self.opendistro_security_plugin)

            # Delete opendistro_security configuration entries from
            # elasticsearch.yml file.
            file_contents = Elasticsearch.read_file_contents(
                self.elasticsearch_config_path)
            flag = 1
            start_line = "######## Start OpenDistro"
            end_line = "######## End OpenDistro"
            with open(self.elasticsearch_config_path, "w") as f:
                for line in file_contents:
                    if line.startswith(start_line):
                        flag = 0
                    if line.startswith(end_line):
                        flag = 1
                    if flag and not line.startswith(end_line):
                        f.write(line)
                f.close()

        except OSError as e:
            msg = f"Exception in in post_install {e}."
            Log.error(msg)
            raise
        Log.info("Post_install done.")
        return 0

    def config(self):
        """
        Performs configurations.

        Raises exception on error
        """
        try:
            # Create backup of elasticsearch_config file.
            if not os.path.exists(
                    f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp'):
                shutil.copyfile(
                    self.elasticsearch_config_path,
                    f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp')
            else:
                shutil.copyfile(
                    f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp',
                    self.elasticsearch_config_path
                    )
            # Get config entries that needs to add in elasticsearch.yml
            config_to_add = self.get_config_entries()
            file_contents = Elasticsearch.read_file_contents(
                self.elasticsearch_config_path)
            with open(self.elasticsearch_config_path, "a+") as f:
                for line in config_to_add:
                    f.write(f'\n{line}')
                f.close()

            # load omelasticsearch module in rsyslog.
            file_contents = Elasticsearch.read_file_contents(self.rsyslog_conf)
            insert_line = 'module(load="omelasticsearch")'
            if not any(insert_line in i for i in file_contents):
                with open(self.rsyslog_conf, "w") as f:
                    for line in file_contents:
                        if line == '\n':
                            continue
                        f.write(f'\n{line}')
                        if line.strip('\n') == "#### MODULES ####":
                            f.write(f'\n{insert_line}\n')
                    f.close()

            try:
                service_obj = Service('rsyslog.service')
                service_obj.restart()
            except ServiceError as e:
                msg = f"Restarting rsyslog.service failed due to error, {e}."
                Log.error(msg)

        except(Exception, OSError) as e:
            msg = f"Failed in config stage due to error {e}."
            Log.error(msg)
            raise

        Log.info("Config done.")
        return 0

    def reset(self):
        """
        Performs reset.

        Raises exception on error
        """
        # Check service status
        service_obj = Service('elasticsearch.service')
        service_state = service_obj.get_state()
        if service_state._state == 'active':
            Log.warn(
                "Elasticsearch service in active state. \n"
                "Stopping Elasticsearch service now...")
            service_obj.stop()

        # Clear log files.
        Elasticsearch.truncate_log_files(self.log_path)
        Log.info("Reset done.")
        return 0

    def cleanup(self, pre_factory=False):
        """
        Performs cleanup.

        Raises exception on error
        """
        # Reset config.
        if os.path.exists(
                f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp'):
            shutil.copyfile(
                f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp',
                self.elasticsearch_config_path)
            self.delete_path(
                f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp')

        if pre_factory:
            # No action needed,
            # log and data directory for Elasticsearch got cleared during
            # elasticsearch-oss,opendistro rpms removal.
            Log.info("No action needed for --pre-factory.")
        Log.info("Cleanup done.")
        return 0

    def prepare(self):
        """Perform prepare, Raises exception on error."""
        Log.info("No action needed for Prepare Miniprovisioner Interface.")
        return 0

    def init(self):
        """Perform init, Raises exception on error."""
        Log.info("No action needed for Init Miniprovisioner Interface.")
        return 0

    def pre_upgrade(self):
        """
        Perform pre_upgrade.

        Raises exception on error
        """
        Log.info("No action needed for Pre_upgrade Miniprovisioner Interface.")
        return 0

    def post_upgrade(self):
        """
        Perform post_upgrade.

        Raises exception on error
        """
        Log.info("No action needed for Post_upgrade Miniprovisioner Interface.")
        return 0

    def test(self):
        """
        Perform configuration testing.

        Raises exception on error
        """
        Log.info("Test starting...")
        unittest.TextTestRunner().run(
            unittest.TestLoader().loadTestsFromTestCase(
                self.get_test_module()))
        Log.info("Test done.")
        return 0

    def get_test_module(self):
        try:
            from cortx.utils.test.elasticsearch.test_elasticsearch import ElasticsearchTest
        except ImportError:
            class ElasticsearchTest(unittest.TestCase):
                def runTest(self):
                    print("Install cortx-py-utils-test to run test")

        return ElasticsearchTest

    def get_config_entries(self):
        """Returns config that needs to add in elasticsearch.yml file."""
        # Read required config from provisioner config.
        srvnodes = []
        server_nodes_id = []
        machine_id = Conf.machine_id
        node_name = Conf.get(self.index, f'server_node>{machine_id}>name')
        # Total nodes in cluster.
        cluster_id = Conf.get(
            self.index, f'server_node>{machine_id}>cluster_id')
        if cluster_id is None:
            raise ElasticsearchSetupError(errno.EINVAL, "cluster_id is none.")
        storage_set = Conf.get(
            self.index, f'cluster>{cluster_id}>storage_set')
        if storage_set:
            server_nodes_id = storage_set[0]["server_nodes"]
        if server_nodes_id:
            for machine_id in server_nodes_id:
                srvnodes.append(
                    Conf.get(self.index, f'server_node>{machine_id}>name'))

        # Config entries needs to add in elasticsearch.yml file.
        config_entries = [
            f"cluster.name: {self.elasticsearch_cluster_name}",
            f"node.name: {node_name}",
            f"network.bind_host: {['localhost', node_name]}",
            f"network.publish_host: {[node_name]}",
            f"discovery.seed_hosts: {srvnodes}",
            f"cluster.initial_master_nodes: {srvnodes}",
            f"http.port: {self.http_port}"
            ]
        return config_entries

    @staticmethod
    def read_file_contents(filename):
        """Performs read operation on file."""
        if not os.path.exists(filename):
            raise OSError(f"{filename} file not found.")
        with open(filename, "r") as f:
            lines = f.readlines()
            f.close()
        return lines

    @staticmethod
    def delete_path(path):
        """Delete file or directory."""
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def truncate_log_files(path):
        """Truncate log files."""
        if os.path.exists(path):
            for root, _, files in os.walk(path):
                for file in files:
                    cmd = f"truncate -s 0 > {os.path.join(root, file)}"
                    _, err, rc = SimpleProcess(cmd).run()
                    if rc != 0:
                        Log.error(
                                "Failed to clear file data. "
                                f"ERROR:{err} CMD:{cmd}")
