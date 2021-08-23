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

from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.service import DbusServiceHandler
from cortx.utils.validator.error import VError
from cortx.utils.service.service_handler import ServiceError

from .test import ElasticsearchTest


class ElasticsearchSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" % (
            self._rc, self._desc, traceback.format_exc())

    def rc(self):
        return self._rc


class Elasticsearch:
    """ Represents Elasticsearch and Performs setup related actions """

    index = "Elasticsearch"
    elasticsearch_config_path = "/etc/elasticsearch/elasticsearch.yml"
    log_path = "/var/log/elasticsearch"
    data_path = "/var/lib/elasticsearch"
    elasticsearch_file_path = "/opt/seagate/cortx/utils/conf/elasticsearch/"

    Log.init(
        'ElasticsearchProvisioning',
        '/var/log/cortx/utils/elasticsearch',
        level='DEBUG')

    def __init__(self, conf_url):
        Conf.load(self.index, conf_url)

    def validate(self, phase: str):
        """ Perform validations. Raises exceptions if validation fails """

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
                msg = "Validation failed for %s phase with error %s" % (
                    phase, e)
                Log.error(msg)
                raise
        return 0

    def post_install(self):
        """ Performs post install operations. Raises exception on error """

        opendistro_security_plugin = "/usr/share/elasticsearch/plugins/opendistro_security"

        try:
            # Remove opendistro_security plugins.
            Elasticsearch.delete_path(opendistro_security_plugin)

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
            msg = "Exception in in post_install %s" % (e)
            Log.error(msg)
            raise
        Log.info("Post_install done.")
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """

        try:
            rsyslog_conf = "/etc/rsyslog.conf"

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
            file_contents = Elasticsearch.read_file_contents(rsyslog_conf)
            insert_line = 'module(load="omelasticsearch")'
            if not any(insert_line in i for i in file_contents):
                with open(rsyslog_conf, "w") as f:
                    for line in file_contents:
                        if line == '\n':
                            continue
                        f.write(f'\n{line}')
                        if line.strip('\n') == "#### MODULES ####":
                            f.write(f'\n{insert_line}\n')
                    f.close()

            try:
                DbusServiceHandler().restart('rsyslog.service')
            except ServiceError as err:
                msg = "Restarting rsyslog.service failed due to error, %s" % err
                Log.error(msg)
                raise

        except(Exception, OSError ) as e:
            msg = "Failed in config stage due to error %s" % (e)
            Log.error(msg)
            raise

        Log.info("Config done.")
        return 0

    def reset(self):
        """ Performs Configuration reset. Raises exception on error """

        # Check service status
        service_state = DbusServiceHandler().get_state('elasticsearch.service')
        if service_state._state == 'active':
            Log.warn("Elasticsearch service in active state.")
            Log.warn("Stopping Elasticsearch service now...")
            DbusServiceHandler().stop('elasticsearch.service')

        # Remove data directory.
        Elasticsearch.delete_path(self.data_path)
        # Clear log files.
        Elasticsearch.truncate_log_files(self.log_path)
        Log.info("Reset done.")
        return 0

    def cleanup(self, pre_factory=False):
        """ Performs Configuration reset. Raises exception on error """

        # Reset config.
        if not os.path.exists(
                f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp'):
            shutil.copyfile(
                f'{self.elasticsearch_file_path}/elasticsearch.yml.bkp',
                self.elasticsearch_config_path)

        if pre_factory:
            # Remove elasticsearch and opendistro package.
            cmd = "sudo rpm -e --nodeps opendistroforelasticsearch elasticsearch-oss \
                opendistro-sql opendistro-alerting opendistro-anomaly-detection \
                opendistro-index-management opendistro-job-scheduler \
                opendistro-knn opendistro-knnlib opendistro-performance-analyzer \
                opendistro-reports-scheduler opendistro-security"

            _, err, rc = SimpleProcess(cmd).run()
            if rc != 0:
                msg = "Error while removing packages, Error: %s" % err
                Log.error(msg)
                raise ElasticsearchSetupError(errno.EINVAL, msg)
            # Remove data and log and config directory.
            for path in [self.log_path, self.data_path, '/etc/elasticsearch']:
                Elasticsearch.delete_path(path)
        Log.info("Cleanup done.")
        return 0

    def prepare(self):
        """ Perform initialization. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def test(self, plan, config):
        """ Perform configuration testing. Raises exception on error """

        Log.info("Test starting...")
        ElasticsearchTest(config, plan)
        Log.info("Test done.")
        return 0

    def get_config_entries(self):
        """ Returns config that needs to add in elasticsearch.yml file. """
        # Read required config from provisioner config.
        srvnodes = []
        server_nodes_id = []
        elasticsearch_cluster_name = "elasticsearch_cluster"
        http_port = 9200
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
            for id in server_nodes_id:
                srvnodes.append(
                    Conf.get(self.index, f'server_node>{id}>name'))

        # Config entries needs to add in elasticsearch.yml file.
        config_entries = [
            f"cluster.name: {elasticsearch_cluster_name}",
            f"node.name: {node_name}",
            f"network.bind_host: {['localhost', node_name]}",
            f"network.publish_host: {[node_name]}",
            f"discovery.seed_hosts: {srvnodes}",
            f"cluster.initial_master_nodes: {srvnodes}",
            f"http.port: {http_port}"
            ]
        return config_entries

    @staticmethod
    def read_file_contents(filename):
        """Performs read operation on file."""
        if not os.path.exists(filename):
            raise OSError("%s file not found." % filename)
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
                    file = open(file, "w")
                    file.truncate()
                    file.close()
