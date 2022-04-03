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
import glob
import json
import errno
from pathlib import Path

from cortx.utils import errors
from cortx.utils import const
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.common import SetupError, DbConf
from cortx.utils.errors import TestFailed
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError
from cortx.utils.validator.v_confkeys import ConfKeysV
from cortx.utils.service.service_handler import Service


class Utils:
    """ Represents Utils and Performs setup related actions """
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
        """
        Restart rsyslog service for reflecting supportbundle rsyslog config
        """
        try:
            Log.info("Restarting rsyslog service")
            service_obj = Service("rsyslog.service")
            service_obj.restart()
        except Exception as e:
            Log.warn(f"Error in rsyslog service restart: {e}")

    @staticmethod
    def _copy_database_conf(config_path: str):
        """Copy database configuration from provided source to Consul KV"""
        DbConf.init(config_path)
        DbConf.import_database_conf(f'yaml://{Utils.utils_path}/conf/database.yaml')

    @staticmethod
    def validate(phase: str):
        """ Perform validtions """

        # Perform RPM validations
        pass

    @staticmethod
    def post_install(config_path: str):
        """ Performs post install operations """
        # Check required python packages
        # TODO: Remove this python package check as RPM installation
        # doing the same.
        with open(f"{Utils.utils_path}/conf/python_requirements.txt") as file:
            req_pack = []
            for package in file.readlines():
                pack = package.strip().split('==')
                req_pack.append(f"{pack[0]} ({pack[1]})")
        try:
            with open(f"{Utils.utils_path}/conf/python_requirements.ext.txt") as extfile :
                for package in extfile.readlines():
                    pack = package.strip().split('==')
                    req_pack.append(f"{pack[0]} ({pack[1]})")
        except Exception:
             Log.info("Not found: "+f"{Utils.utils_path}/conf/python_requirements.ext.txt")

        PkgV().validate(v_type='pip3s', args=req_pack)
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
        config_template_index = 'config'
        Conf.load(config_template_index, config_path)

        # set cluster nodename:hostname mapping to cluster.conf
        Utils._copy_cluster_map(config_path)
        Utils._configure_rsyslog()
        return 0

    @staticmethod
    def init(config_path: str):
        """ Perform initialization """
        # Create message_type for Event Message
        from cortx.utils.message_bus import MessageBus, MessageBusAdmin
        from cortx.utils.message_bus.error import MessageBusError
        try:
            # Read the config values
            Conf.load('config', config_path, skip_reload=True)
            message_bus_backend = Conf.get('config', \
                'cortx>utils>message_bus_backend')
            message_server_endpoints = Conf.get('config', \
                f'cortx>external>{message_bus_backend}>endpoints')
            MessageBus.init(message_server_endpoints)
            admin = MessageBusAdmin(admin_id='register')
            admin.register_message_type(message_types=['IEM', \
                'audit_messages'], partitions=1)
        except MessageBusError as e:
            if 'TOPIC_ALREADY_EXISTS' not in e.desc:
                raise SetupError(e.rc, "Unable to create message_type. %s", e)

        return 0

    @staticmethod
    def test(config_path: str, plan: str):
        """ Perform configuration testing """
        # Runs cortx-py-utils unittests as per test plan
        try:
            Log.info("Validating cortx-py-utils-test rpm")
            PkgV().validate('rpms', ['cortx-py-utils-test'])
            import cortx.utils.test as test_dir
            plan_path = os.path.join(os.path.dirname(test_dir.__file__), \
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
            from cortx.utils.message_bus import MessageBusAdmin, MessageBus
            from cortx.utils.message_bus import MessageProducer
            Conf.load('config', config_path, skip_reload=True)
            message_bus_backend = Conf.get('config', \
                'cortx>utils>message_bus_backend')
            message_server_endpoints = Conf.get('config', \
                f'cortx>external>{message_bus_backend}>endpoints')
            MessageBus.init(message_server_endpoints)
            mb = MessageBusAdmin(admin_id='reset')
            message_types_list = mb.list_message_types()
            if message_types_list:
                for message_type in message_types_list:
                    producer = MessageProducer(producer_id=message_type, \
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
            from cortx.utils.message_bus import MessageBus, MessageBusAdmin
            Conf.load('config', config_path, skip_reload=True)
            message_bus_backend = Conf.get('config', \
                'cortx>utils>message_bus_backend')
            message_server_endpoints = Conf.get('config', \
                f'cortx>external>{message_bus_backend}>endpoints')
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
    def upgrade(config_path: str):
        """Perform upgrade steps."""
        # ToDo - in future, for utils/message server config changes may be
        # required during upgrade phase.
        # Currently no config changes required.
        return 0

    @staticmethod
    def pre_upgrade(level: str):
        """ pre upgrade hook for node and cluster level """
        if level == 'node':
            # TODO Perform corresponding actions for node
            pass
        elif level == 'cluster':
            # TODO Perform corresponding actions for cluster
            pass
        return 0

    @staticmethod
    def post_upgrade(level: str):
        """ post upgrade hook for node and cluster level """
        if level == 'node':
            # TODO Perform corresponding actions for node
            pass
        elif level == 'cluster':
            # TODO Perform corresponding actions for cluster
            pass
        return 0
