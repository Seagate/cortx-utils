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
import fileinput
import traceback
from socket import gethostname, gethostbyname
from pwd import getpwnam as get_user_by_name
from grp import getgrnam as get_group_by_name

from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.errors import UtilsError
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.message_bus import MessageBrokerFactory

class KafkaSetupError(UtilsError):
    """Generic Exception with error code and output."""
    def __init__(self, rc, message, *args):
        super().__init__(rc, message, *args)


class Kafka:
    """Represents Kafka and Performs setup related actions."""
    input_config_index = 'kafka_config'

    def __init__(self, conf_url):
        Conf.load(self.input_config_index, conf_url)

    @staticmethod
    def _kafka_rpm_installed() -> bool:
        """
        Checks if kafka rpm is installed on the node

        Returns:
            bool: True if installed else False
        """
        try:
            PkgV().validate('rpms', ['kafka'])
            return True
        except Exception:
            return False

    @staticmethod
    def _kafka_user_and_group_exists() -> bool:
        """Checks if kafka user and kafka group exists in linux pwd database

        Returns:
            bool: Returns True if kafka user and group present else False
        """
        try:
            kafka_user = get_user_by_name('kafka')
        except KeyError:
            return False

        try:
            kafka_group = get_group_by_name('kafka')
        except KeyError:
            return False

        # Check if groupid for both, user and group is same
        if kafka_group.gr_gid != kafka_user.pw_gid:
            return False
        return True

    @staticmethod
    def _set_kafka_user_and_group():
        """Creates kafka user and group

        Raises:
            KafkaSetupError: if any command produces undesired return code
        """
        cmds = [
            "adduser kafka",
            "usermod -aG wheel kafka",
            "echo \"kafka ALL=(ALL) NOPASSWD: ALL\" >> /etc/sudoers.d/90-cloud-init-users",
            "groupadd --force kafka",
            "usermod --append --groups kafka kafka"]
        for cmd in cmds:
            _, _, rc = SimpleProcess(cmd).run()
            # rc 9 if kafka user already exists & 12 if kafka user created
            if rc not in (0, 9, 12):
                raise KafkaSetupError(
                    errno.EINVAL,"Failed in creating kafka user and group")
    @staticmethod
    def _set_kafka_multi_node_config(hostname: list, port: list,
        kafka_server: str) -> int:
        """
        Sets configration of kafka multi-node

        Args:
            hostname (list): hostname/ip of node
            port (list): kafka server port
            kafka_Server: host name of active kafka server 

        Returns:
            int: Returns 0 after successfully updating properties
        """

        kafka._set_kafka_single_node_config(hostname, port)
        server_properties_file = '/opt/kafka/config/server.properties'
        zookeeper_connect = ", ".join(f'{h}:2181' for h in hostname)
        server_properties = {'zookeeper.connect': zookeeper_connect}
        
        zookeeper_properties_file = '/opt/kafka/config/zookeeper.properties'
        zookeeper_properties={
            'tickTime': 2000,
            'initLimit': 10,
            'syncLimit': 5,
            'clientPort': 2181,
            'autopurge.snapRetainCount': 3,
            'autopurge.purgeInterval': 24
        }
        myid = None
        for hst_ind in range(len(hostname)):
            host = hostname[hst_ind]
            zookeeper_properties[f'server.{hst_ind + 1}'] = f'{host}:2888:3888'
            if host == kafka_server:
                server_properties['broker.id'] = hst_ind - 1
                # /var/lib/zookeeper myid file
                with open('/var/lib/zookeeper', 'a') as f:
                        fd.write(hst_ind)

        # update kafka server properties file
        Kafka._update_properties_file(
            server_properties_file, server_properties)
        # Update Zookeeper properties file
        Kafka._update_properties_file(
            zookeeper_properties_file,zookeeper_properties)
        
        return 0

    @staticmethod
    def _set_kafka_single_node_config(hostname, port):
        """
        Sets configration for kafka

        Args:
            hostname (str): hostname/ip of node
            port (str): kafka server port

        Returns:
            int: Returns 0 after successfully updating properties
        """
        server_properties_file = '/opt/kafka/config/server.properties'
        server_properties = {
            'listeners': f'PLAINTEXT://{hostname}:{port}',
            'log.flush.offset.checkpoint.interval.ms': '1',
            'log.retention.check.interval.ms': '1',
            'log.dirs': '/var/log/kafka',
            'log.delete.delay.ms': '1',
        }
        Kafka._update_properties_file(
            server_properties_file, server_properties)

        zookeeper_properties_file = '/opt/kafka/config/zookeeper.properties'
        zookeeper_properties={
            'dataLogDir': '/var/log/zookeeper',
            'dataDir': '/var/lib/zookeeper'
        }
        Kafka._update_properties_file(
            zookeeper_properties_file,zookeeper_properties)

        directories = [
            server_properties['log.dirs'],
            zookeeper_properties['dataDir'],
            zookeeper_properties['dataLogDir']]
        for directory in directories:
            Kafka._create_dir_and_set_kafka_ownership(directory)
        return 0

    @staticmethod
    def _create_dir_and_set_kafka_ownership(directory:str):
        """Creats directory if dosent exist and changes ownership to kafka:kafka

        Args:
            directory (str): directort to be created

        Returns:
            int: Returns 0 on success
        """
        try:
            os.makedirs(directory,exist_ok=True)
            os.system(f"chown -R kafka:kafka {directory}")
        except Exception as e:
            raise KafkaSetupError(rc=errno.EINVAL, message=e)

        return 0

    @staticmethod
    def _update_properties_file(file_path: str, properties: dict):
        """Updates/Add properties in provided file while retaining comments

        Args:
            properties (dict): Key value pair of properies to be updated
            file_path (str): absolute path to properties file
        """
        pending_config=[]
        for key, val in properties.items():
            key_found = False
            with fileinput.input(files=(file_path), inplace=True) as fp:
                # inplace=True argument redirects print output to file
                for line in fp:
                    if line.startswith(key):
                        key_found = True
                        print(f"{key}={val}")
                    else:
                        print(line, end='')

            if not key_found:
                        pending_config.append(f'{key}={val}\n')
        with open(file_path, 'a') as fd:  # Append remaining new keys to file
            for item in pending_config:
                fd.write(item)

    def validate(self, phase: str):
        """Perform validtions. Raises exceptions if validation fails."""

        # Perform RPM validations
        return

    def post_install(self):
        """
        Performs post install operations. Raises KafkaSetupError on error

        Raises:
            KafkaSetupError: If Kafka rpm is not installed
            KafkaSetupError: If kafka user and kafka group does not exists

        Returns:
            [type]: [description]
        """
        if not Kafka._kafka_rpm_installed():
            Log.info("Kafka rpm not installed")

        if not Kafka._kafka_user_and_group_exists():
            Log.info("Kafka user group dosen't exists")

        return 0

    def prepare(self):
        """Perform prepration. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def init(self):
        """Perform initialization. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def config(self):
        """Performs configurations. Raises exception on error."""
        if not Kafka._kafka_rpm_installed():
            raise KafkaSetupError(errno.EINVAL,"Kafka rpm not installed")

        if not Kafka._kafka_user_and_group_exists():
            Kafka._set_kafka_user_and_group()

        servers, ports = \
            MessageBrokerFactory.get_server_list(self.input_config_index)
        # Proceed with configration change if current node in kafka server list,
        # rpm is installed and kafka user and group created
        curr_host_fqdn = gethostname()
        curr_host_ip = gethostbyname(curr_host_fqdn)
        single_node_pre_config_checks = len(servers) == 1 \
            and (servers[0] in [curr_host_fqdn, curr_host_ip])

        if single_node_pre_config_checks:
            Kafka._set_kafka_single_node_config(servers[0], ports[0])
        elif len(servers) > 1
            for host, prt in zip(servers, ports):
                if host in  [curr_host_fqdn, curr_host_ip]:
                    # multi node setup
                    Kafka._set_kafka_multi_node_config(servers, prt, host)

        return 0

    def test(self, plan):
        """Perform configuration testing. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def reset(self):
        """Performs Configuraiton reset. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0
