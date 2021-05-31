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
import json
import errno
from cortx.utils import errors
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError
from cortx.utils.validator.v_service import ServiceV
from cortx.utils.validator.v_confkeys import ConfKeysV
from cortx.utils.message_bus.error import MessageBusError


Log.init('utils_setup', '/var/log/cortx/utils', level='INFO', backup_count=5,\
         file_size_in_mb=5)


class SetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0:
            return self._desc
        return "error(%d): %s" % (self._rc, self._desc)


class Utils:
    """ Represents Utils and Performs setup related actions """

    @staticmethod
    def _create_msg_bus_config(kafka_server_list: list, port_list: list):
        """ Create the config file required for message bus """

        conf_file = '/etc/cortx/message_bus.conf'
        with open(f'{conf_file}.sample', 'w+') as file:
            json.dump({}, file, indent=2)
        try:
            pre_servers = []
            if os.path.exists(conf_file):
                Conf.load('pre_index', f'json://{conf_file}')
                pre_servers = Conf.get('pre_index', 'message_broker>cluster')
            Conf.load('index', f'json://{conf_file}.sample')
            Conf.set('index', 'message_broker>type', 'kafka')
            servers = [{'server': kafka_server_list[i], 'port': port_list[i]}
                       for i in range(len(kafka_server_list)) if
                       {'server': kafka_server_list[i],
                        'port': port_list[i]} not in pre_servers]
            servers.extend(pre_servers)
            Conf.set('index', 'message_broker>cluster', servers)
            Conf.save('index')
        except ConfError as e:
            SetupError(e.rc, "Unable to load servers from config file %s %s",\
                conf_file, e)
        except Exception as e:
            SetupError(errors.ERR_OP_FAILED, "Unable to load servers from "\
                "config file %s %s", conf_file, e)
        # copy this conf file as message_bus.conf
        try:
            os.rename(f'{conf_file}.sample', conf_file)
        except OSError as e:
            raise SetupError(e.errno, "Failed to create %s %s", conf_file, e)

    @staticmethod
    def _get_kafka_server_list(conf_url: str):
        """ Reads the ConfStore and derives keys related to message bus """
        Conf.load('cluster_config', conf_url)
        key_list = ['cortx>software>common>message_bus_type',
                   'cortx>software>kafka>servers']
        ConfKeysV().validate('exists', 'cluster_config', key_list)
        msg_bus_type = Conf.get('cluster_config', key_list[0])
        if msg_bus_type != 'kafka':
            Log.error(f"Message bus type {msg_bus_type} does not support" \
                      f" message bus ")
            raise SetupError(errno.EINVAL, "Message Bus do not support " +\
                "type %s" % msg_bus_type)
        # Read the required keys
        all_servers = Conf.get('cluster_config', key_list[1])
        no_servers = len(all_servers)
        kafka_server_list = []
        port_list = []
        for i in range(no_servers):
            # check if port is mentioned
            rc = all_servers[i].find(':')
            if rc == -1:
                port_list.append('9092')
                kafka_server_list.append(all_servers[i])
            else:
                port_list.append(all_servers[i][rc + 1:])
                kafka_server_list.append(all_servers[i][:rc])
        if len(kafka_server_list) == 0:
            Log.error(f"Missing config entry {key_list} in config file "\
                f"{conf_url}")
            raise SetupError(errno.EINVAL, "Missing config entry %s in config"
                " file %s", key_list, conf_url)
        return kafka_server_list, port_list

    @staticmethod
    def _get_server_info(conf_url: str, machine_id: str) -> dict:
        """ Reads the ConfStore and derives keys related to Event Message """

        Conf.load('server_info', conf_url)
        key_list = [f'server_node>{machine_id}']
        ConfKeysV().validate('exists', 'server_info', key_list)
        server_info = Conf.get('server_info', key_list[0])
        return server_info

    @staticmethod
    def _create_cluster_config(server_info: dict):
        """ Create the config file required for Event Message """

        conf_file = '/etc/cortx/cluster.conf'
        try:
            if os.path.exists(conf_file):
                Conf.load('cluster', f'json://{conf_file}')
                for key, value in server_info.items():
                    Conf.set('cluster', f'server_node>{key}', value)
                Conf.save('cluster')
            else:
                with open(f'{conf_file}', 'w+') as file:
                    json.dump({}, file, indent=2)
                Conf.load('cluster', f'json://{conf_file}')
                for key, value in server_info.items():
                    Conf.set('cluster', f'server_node>{key}', value)
                Conf.save('cluster')
        except ConfError as e:
            raise SetupError(e.rc, "Unable to create cluster config file "\
                "%s %s", conf_file, e)
        except Exception as e:
            raise SetupError(errors.ERR_OP_FAILED, "Unable to create cluster"\
                " config file %s %s", conf_file, e)

    @staticmethod
    def validate(phase: str):
        """ Perform validtions """

        # Perform RPM validations
        pass

    @staticmethod
    def post_install():
        """ Performs post install operations """

        # check whether zookeeper and kafka are running
        ServiceV().validate('isrunning', ['kafka-zookeeper.service', \
            'kafka.service'])
        # Check python packages installed
        with open('/opt/seagate/cortx/utils/conf/requirements.txt') as f:
            packages = f.readlines()
            packages = [
                f"{pkg.strip().split('==')[0]} ({pkg.strip().split('==')[1]})"
                for pkg in packages]
            from cortx.utils.validator.v_pkg import PkgV
            PkgV().validate(v_type='pip3s', args=packages)
        return 0

    @staticmethod
    def init():
        """ Perform initialization """

        # Create message_type for Event Message
        from cortx.utils.message_bus import MessageBusAdmin
        try:
            admin = MessageBusAdmin(admin_id='register')
            admin.register_message_type(message_types=['IEM'], partitions=1)
        except MessageBusError as e:
            raise SetupError(e.rc, "Unable to create message_type. %s", e)
        return 0

    @staticmethod
    def config(conf_url: str):
        """ Performs configurations """
        # Message Bus Config
        kafka_server_list, port_list = Utils._get_kafka_server_list(conf_url)
        if kafka_server_list is None:
            Log.error(f"Could not get kafka server info. from {conf_url}")
            raise SetupError(errno.EINVAL, "Could not find kafka server " +\
                "information in %s", conf_url)
        Utils._create_msg_bus_config(kafka_server_list, port_list)
        # Cluster config
        server_info = Utils._get_server_info(conf_url, Conf.machine_id)
        if server_info is None:
            Log.error(f"Could not get server information from {conf_url}")
            raise SetupError(errno.EINVAL, "Could not find server " +\
                "information in %s", conf_url)
        Utils._create_cluster_config(server_info)
        return 0

    @staticmethod
    def test():
        """ Perform configuration testing """
        from cortx.setup import MessageBusTest
        msg_test = MessageBusTest()
        # Send a message
        msg_test.send_msg(["Test Message"])
        # Recieve the same & validate
        msg = msg_test.receive_msg()
        if str(msg.decode('utf-8')) != "Test Message":
            Log.error("Could not test utils config, fails in matching sent " +\
                "and received message.")
            raise SetupError(errno.EINVAL, "Unable to test the config. Received\
                message is %s", msg)
        return 0

    @staticmethod
    def reset():
        """ Remove/Delete all the data that was created after post install """
        conf_file = '/etc/cortx/message_bus.conf'
        if os.path.exists(conf_file):
            # delete message_types
            from cortx.utils.message_bus import MessageBusAdmin
            try:
                mb = MessageBusAdmin(admin_id='reset')
                message_types_list = mb.list_message_types()
                if message_types_list:
                    mb.deregister_message_type(message_types_list)
            except MessageBusError as e:
                raise SetupError(e.rc, "Can not reset Message Bus. %s", e)
            except Exception as e:
                raise SetupError(errors.ERR_OP_FAILED, "Can not reset Message  \
                    Bus. %s", e)
        return 0

    @staticmethod
    def cleanup():
        """ Cleanup configs and logs. """
        config_files = ['/etc/cortx/message_bus.conf', \
            '/etc/cortx/cluster.conf']
        for each_file in config_files:
            if os.path.exists(each_file):
                # delete data/config stored
                try:
                    os.remove(each_file)
                except OSError as e:
                    raise SetupError(e.errno, "Error deleting config file %s, \
                        %s", each_file, e)
        return 0
