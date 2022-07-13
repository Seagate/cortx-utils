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

from cortx.utils import errors
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.common import SetupError, DbConf
from cortx.utils.errors import TestFailed
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError
from cortx.utils.validator.v_confkeys import ConfKeysV
from cortx.utils.service.service_handler import Service
from cortx.utils.const import ( GCONF_INDEX, MSG_BUS_BACKEND_KEY, EXTERNAL_KEY,
    CHANGED_PREFIX ,NEW_PREFIX, DELETED_PREFIX, DELTA_INDEX )


class Utils:
    """Represents Utils and Performs setup related actions."""

    utils_path = '/opt/seagate/cortx/utils'

    # Utils private methods

    @staticmethod
    def _copy_cluster_map(config_path: str):
        Conf.load('cluster', config_path, skip_reload=True)
        cluster_data = Conf.get('cluster', 'node')
        for _, node_data in cluster_data.items():
            hostname = node_data.get('hostname')
            node_name = node_data.get('name')
            Conf.set('cluster', f'cluster>{node_name}', hostname)
        Conf.save('cluster')

    @staticmethod
    def _configure_rsyslog():
        """Restart rsyslog service for reflecting supportbundle rsyslog config."""
        try:
            Log.info("Restarting rsyslog service")
            service_obj = Service("rsyslog.service")
            service_obj.restart()
        except Exception as e:
            Log.warn(f"Error in rsyslog service restart: {e}")

    @staticmethod
    def _copy_database_conf(config_path: str):
        """Copy database configuration from provided source to Consul KV."""
        DbConf.init(config_path)
        DbConf.import_database_conf(f'yaml://{Utils.utils_path}/conf/database.yaml')

    @staticmethod
    def validate(phase: str):
        """Perform validtions."""
        # Perform RPM validations
        pass

    @staticmethod
    def post_install(config_path: str):
        """Performs post install operations."""
        default_sb_path = '/var/log/cortx/support_bundle'
        os.makedirs(default_sb_path, exist_ok=True)

        post_install_template_index = 'post_install_index'
        Conf.load(post_install_template_index, config_path)

        machine_id = Conf.machine_id
        key_list = [f'node>{machine_id}>hostname', f'node>{machine_id}>name']
        ConfKeysV().validate('exists', post_install_template_index, key_list)

        #set cluster nodename:hostname mapping to cluster.conf (needed for Support Bundle)
        Utils._copy_cluster_map(config_path)
        Utils._copy_database_conf(config_path)

        return 0

    @staticmethod
    def config(config_path: str):
        """Performs configurations."""
        # Load required files
        Conf.load(GCONF_INDEX, config_path)

        # set cluster nodename:hostname mapping to cluster.conf
        Utils._copy_cluster_map(config_path) # saving node and host from gconf
        Utils._configure_rsyslog()
        return 0

    @staticmethod
    def init(config_path: str):
        """Perform initialization."""
        # Create message_type for Event Message
        from cortx.utils.message_bus import MessageBus, MessageBusAdmin
        from cortx.utils.message_bus.error import MessageBusError
        try:
            # Read the config values
            # use gconf to create IEM topic
            Conf.load(GCONF_INDEX, config_path, skip_reload=True)
            message_bus_backend = Conf.get(GCONF_INDEX, MSG_BUS_BACKEND_KEY)
            message_server_endpoints = Conf.get(GCONF_INDEX,\
                f'{EXTERNAL_KEY}>{message_bus_backend}>endpoints')
            MessageBus.init(message_server_endpoints)
            admin = MessageBusAdmin(admin_id='register')
            admin.register_message_type(message_types=['IEM',\
                'audit_messages'], partitions=1)
        except MessageBusError as e:
            if 'TOPIC_ALREADY_EXISTS' not in e.desc:
                raise SetupError(e.rc, "Unable to create message_type. %s", e)

        return 0

    @staticmethod
    def test(config_path: str, plan: str):
        """Perform configuration testing."""
        # Runs cortx-py-utils unittests as per test plan
        try:
            Log.info("Validating cortx-py-utils-test rpm")
            PkgV().validate('rpms', ['cortx-py-utils-test'])
            import cortx.utils.test as test_dir
            plan_path = os.path.join(os.path.dirname(test_dir.__file__),\
                'plans/', plan + '.pln')
            Log.info("Running test plan: %s", plan)
            cmd = "%s/bin/run_test -c %s -t %s" %(Utils.utils_path, config_path, plan_path)
            _output, _err, _rc = SimpleProcess(cmd).run(realtime_output=True)
            if _rc != 0:
                Log.error("Py-utils Test Failed")
                raise TestFailed("Py-utils Test Failed. \n Output : %s "\
                    "\n Error : %s \n Return Code : %s" %(_output, _err, _rc))
        except VError as ve:
            Log.error("Failed at package Validation: %s", ve)
            raise SetupError(errno.EINVAL, "Failed at package Validation:"\
                " %s", ve)
        return 0

    @staticmethod
    def reset(config_path: str):
        """Remove/Delete all the data/logs that was created by user/testing."""
        from cortx.utils.message_bus.error import MessageBusError
        try:
            # use gconf to deregister IEM
            from cortx.utils.message_bus import MessageBusAdmin, MessageBus
            from cortx.utils.message_bus import MessageProducer
            Conf.load(GCONF_INDEX, config_path, skip_reload=True)
            message_bus_backend = Conf.get('config', MSG_BUS_BACKEND_KEY)
            message_server_endpoints = Conf.get('config',\
                f'{EXTERNAL_KEY}>{message_bus_backend}>endpoints')
            MessageBus.init(message_server_endpoints)
            mb = MessageBusAdmin(admin_id='reset')
            message_types_list = mb.list_message_types()
            if message_types_list:
                for message_type in message_types_list:
                    producer = MessageProducer(producer_id=message_type,\
                        message_type=message_type, method='sync')
                    producer.delete()

        except MessageBusError as e:
            raise SetupError(e.rc, "Can not reset Message Bus. %s", e)
        except Exception as e:
            raise SetupError(errors.ERR_OP_FAILED, "Internal error, can not \
                reset Message Bus. %s", e)
        return 0

    @staticmethod
    def cleanup(pre_factory: bool, config_path: str):
        """Remove/Delete all the data that was created after post install."""

        # delete message_types
        from cortx.utils.message_bus.error import MessageBusError
        try:
            # use gconf to clean and delete all message type in messagebus
            from cortx.utils.message_bus import MessageBus, MessageBusAdmin
            Conf.load(GCONF_INDEX, config_path, skip_reload=True)
            message_bus_backend = Conf.get(GCONF_INDEX, MSG_BUS_BACKEND_KEY)
            message_server_endpoints = Conf.get(GCONF_INDEX,\
                f'{EXTERNAL_KEY}>{message_bus_backend}>endpoints')
            MessageBus.init(message_server_endpoints)
            mb = MessageBusAdmin(admin_id='cleanup')
            message_types_list = mb.list_message_types()
            if message_types_list:
                mb.deregister_message_type(message_types_list)
        except MessageBusError as e:
            raise SetupError(e.rc, "Can not cleanup Message Bus. %s", e)
        except Exception as e:
            raise SetupError(errors.ERR_OP_FAILED, "Can not cleanup Message  \
                Bus. %s", e)

        return 0

    @staticmethod
    def upgrade(config_path: str, change_set_path: str):
        """Perform upgrade steps."""


        Conf.load(DELTA_INDEX, change_set_path)
        Conf.load(GCONF_INDEX, config_path, skip_reload=True)
        delta_keys = Conf.get_keys(DELTA_INDEX)

        # if message_bus_backend changed, add new and delete old msg bus entries
        if CHANGED_PREFIX + MSG_BUS_BACKEND_KEY in delta_keys:
            new_msg_bus_backend = Conf.get(DELTA_INDEX,
                CHANGED_PREFIX + MSG_BUS_BACKEND_KEY).split('|')[1]
            Conf.set(GCONF_INDEX, MSG_BUS_BACKEND_KEY, new_msg_bus_backend)
            for key in delta_keys:
                if NEW_PREFIX + EXTERNAL_KEY + new_msg_bus_backend in key:
                    new_key = key.split(NEW_PREFIX)[1]
                    new_val = Conf.get(DELTA_INDEX, key).split('|')[1]
                    Conf.set(GCONF_INDEX, new_key, new_val )
                if DELETED_PREFIX + EXTERNAL_KEY + new_msg_bus_backend in key:
                    delete_key = key.split(DELETED_PREFIX)[1]
                    Conf.delete(GCONF_INDEX, delete_key)

        # update existing messagebus parameters
        else:
            msg_bus_backend = Conf.get(GCONF_INDEX, MSG_BUS_BACKEND_KEY)
            for key in delta_keys:
                if CHANGED_PREFIX + EXTERNAL_KEY + msg_bus_backend in key:
                    new_val = Conf.get(DELTA_INDEX, key).split('|')[1]
                    change_key = key.split(CHANGED_PREFIX)[1]
                    Conf.set(GCONF_INDEX, change_key, new_val)

        Conf.save(GCONF_INDEX)
        Utils.init(config_path)
        return 0

    @staticmethod
    def pre_upgrade(level: str):
        """Pre upgrade hook for node and cluster level."""
        if level == 'node':
            # TODO Perform corresponding actions for node
            pass
        elif level == 'cluster':
            # TODO Perform corresponding actions for cluster
            pass
        return 0

    @staticmethod
    def post_upgrade(level: str):
        """Post upgrade hook for node and cluster level."""
        if level == 'node':
            # TODO Perform corresponding actions for node
            pass
        elif level == 'cluster':
            # TODO Perform corresponding actions for cluster
            pass
        return 0
