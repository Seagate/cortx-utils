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
from time import sleep
from pwd import getpwnam as get_user_by_name
from grp import getgrnam as get_group_by_name
from socket import gethostname, gethostbyname

from cortx.utils.log import Log
from cortx.utils.errors import UtilsError
from cortx.utils.errors import ERR_OP_FAILED
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess


class KafkaSetupError(UtilsError):

    """Generic Exception with error code and output."""
    def __init__(self, rc, message, *args):
        super().__init__(rc, message, *args)


class Kafka:

    """Represents Kafka and Performs setup related actions."""
    input_config_index = 'kafka_config'

    def __init__(self):
        """Class initialisation."""
        pass

    @staticmethod
    def _validate_kafka_installation():
        """validates kafka is installed and kafka user and group are present
        """
        # check kafka package installed
        try:
            PkgV().validate('rpms', ['kafka'])
        except Exception as e:
            raise KafkaSetupError(e.rc, e)

        # check kafak user exists
        try:
            kafka_user = get_user_by_name('kafka')
            kafka_group = get_group_by_name('kafka')
            if kafka_group.gr_gid != kafka_user.pw_gid:
                raise Exception
        except Exception as e:
            # create kafka user and group
            cmds = [
            "adduser kafka",
            "usermod -aG wheel kafka",
            "groupadd --force kafka",
            "usermod --append --groups kafka kafka"]
            for cmd in cmds:
                _, err, rc = SimpleProcess(cmd).run()
                # rc 9 if kafka user already exists & 12 if kafka user created
                if rc not in (0, 9, 12):
                    raise KafkaSetupError(rc, \
                        "Failed in creating kafka user and group", err)

    @staticmethod
    def _create_dir_and_set_kafka_ownership(directory: str):
        """Creats directory if dosent exist and changes ownership to kafka:kafka

        Args:
            directory (str): directory to be created

        Returns:
            int: Returns 0 on success
        """
        try:
            os.makedirs(directory, exist_ok=True)
            os.system(f"chown -R kafka:kafka {directory}")
        except OSError as e:
            raise KafkaSetupError(rc=e.errno, message=e)

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
                    if line.startswith(key+'='):
                        key_found = True
                        print(f"{key}={val}")
                    else:
                        print(line, end='')

            if not key_found:
                        pending_config.append(f'{key}={val}\n')
        with open(file_path, 'a') as fd:  # Append remaining new keys to file
            for item in pending_config:
                fd.write(item)

    @staticmethod
    def _set_kafka_config(hostname: str, port: str, kafka_servers: list):
        """Updates server.properties and zookeeper.properties with required keys

        Args:
            hostname (str): current host name
            port (str): current kafka port
            kafka_servers (list): list of all kafka server fqdn:port in cluster

        Returns:
            int: Returns 0 on success
        """
        server_properties_file = '/opt/kafka/config/server.properties'
        hosts = [server.split(':')[0] if ':' in server else server \
            for server in kafka_servers]
        zookeeper_connect = ", ".join(f'{host}:2181' for host in hosts)
        server_properties = {
            'zookeeper.connect': zookeeper_connect,
            'listeners': f'PLAINTEXT://{hostname}:{port}',
            'log.flush.offset.checkpoint.interval.ms': '1',
            'log.retention.check.interval.ms': '1',
            'log.dirs': '/var/local/data/kafka',
            'log.delete.delay.ms': '1',
        }

        # replication factor is only acceptable in clustered environment
        if len(kafka_servers) > 1:
            server_properties['default.replication.factor'] = 3
            server_properties['transaction.state.log.min.isr'] = 2
            server_properties['offsets.topic.replication.factor'] = 3
            server_properties['transaction.state.log.replication.factor'] = 3

        zookeeper_properties_file = '/opt/kafka/config/zookeeper.properties'
        zookeeper_properties={
            'dataLogDir': '/var/log/zookeeper',
            'dataDir': '/var/lib/zookeeper',
            'tickTime': 2000,
            'initLimit': 10,
            'syncLimit': 5,
            'clientPort': 2181,
            'autopurge.snapRetainCount': 3,
            'autopurge.purgeInterval': 24,
            '4lw.commands.whitelist': '*',
        }

        directories = [
            server_properties['log.dirs'],
            zookeeper_properties['dataDir'],
            zookeeper_properties['dataLogDir']]

        for directory in directories:
            Kafka._create_dir_and_set_kafka_ownership(directory)

        for index, host in enumerate(hosts):
            zookeeper_properties[f'server.{index + 1}'] = f'{host}:2888:3888'
            if host == hostname:
                server_properties['broker.id'] = index
                # /var/lib/zookeeper myid file
                if len(kafka_servers) > 1:
                    with open('/var/lib/zookeeper/myid', 'w+') as myid_f:
                        myid_f.write(str(index + 1))

        Kafka._update_properties_file(
            server_properties_file, server_properties)
        Kafka._update_properties_file(
            zookeeper_properties_file, zookeeper_properties)

        return 0


    def validate(self, *args, **kwargs):
        """Perform validtions. Raises exceptions if validation fails."""

        # Perform RPM validations
        return

    def post_install(self, *args, **kwargs):
        """Performs post install operations. Raises KafkaSetupError on error."""
        try:
            Kafka._validate_kafka_installation()
        except KafkaSetupError as e:
            Log(e)

        return 0

    def prepare(self, *args, **kwargs):
        """Perform prepration. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def init(self, *args, **kwargs):
        """Perform initialization. Raises exception on error."""
        Kafka._validate_kafka_installation()
        kafka_servers = args[0]
        curr_host_fqdn = gethostname()
        curr_host_ip = gethostbyname(curr_host_fqdn)
        hosts = [server.split(':')[0] if ':' in server else server \
            for server in kafka_servers]

        if not (curr_host_fqdn in hosts or curr_host_ip in hosts) :
            return 0   # return if current host is not a kafka server

        _, err, rc = SimpleProcess("systemctl restart kafka-zookeeper").run()
        if rc != 0:
            raise KafkaSetupError(rc, "Unable to start Zookeeper", err)
        attempt = 0
        while attempt <= 100 :
            _, _, rc = SimpleProcess(
                "echo ruok|nc `hostname` 2181|grep imok").run()
            if rc != 0 :
                attempt += 1
                sleep(1)
                continue
            break

        if attempt > 100 :
            raise KafkaSetupError(ERR_OP_FAILED, "Unable to start Zookeeper")

        _, err, rc = SimpleProcess("systemctl restart kafka").run()
        if rc != 0:
            raise KafkaSetupError(rc, "Unable to start Kakfa", err)

        return 0

    def config(self, *args, **kwargs):
        """Performs configurations. Raises exception on error."""
        kafka_servers = args[0]
        curr_host_fqdn = gethostname()
        curr_host_ip = gethostbyname(curr_host_fqdn)

        for server in kafka_servers:
            host, port = server.split(':') if ':' in server \
                else (server, '9092')
            if (host in [curr_host_fqdn, curr_host_ip]):
                Kafka._validate_kafka_installation()
                Kafka._set_kafka_config(host, port, kafka_servers)

        return 0

    def test(self, *args, **kwargs):
        """Perform configuration testing. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def reset(self, *args, **kwargs):
        """Performs Configuraiton reset. Raises exception on error."""

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0
