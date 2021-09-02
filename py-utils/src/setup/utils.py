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
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.common import SetupError
from cortx.utils.errors import TestFailed
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError
from cortx.utils.validator.v_service import ServiceV
from cortx.utils.validator.v_confkeys import ConfKeysV
from cortx.utils.service.service_handler import Service
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.message_bus import MessageBrokerFactory


class Utils:
    """ Represents Utils and Performs setup related actions """

    # Utils private methods


    @staticmethod
    def _delete_files(files: list):
        """
        Deletes the passed list of files

        Args:
            files ([str]): List of files to be deleted

        Raises:
            SetupError: If unable to delete file
        """
        for each_file in files:
            if os.path.exists(each_file):
                try:
                    os.remove(each_file)
                except OSError as e:
                    raise SetupError(e.errno, "Error deleting file %s, \
                        %s", each_file, e)
        return 0

    @staticmethod
    def _get_utils_path() -> str:
        """ Gets install path from cortx.conf and returns utils path """

        config_file_path = "/etc/cortx/cortx.conf"
        Conf.load('config_file', f'yaml:///{config_file_path}')
        install_path = Conf.get(index='config_file', key='install_path')

        if not install_path:
            error_msg = f"install_path not found in {config_file_path}"
            raise SetupError(errno.EINVAL, error_msg)

        return install_path + "/cortx/utils"

    @staticmethod
    def _create_msg_bus_config(message_server_list: list, port_list: list, \
        config: dict):
        """ Create the config file required for message bus """

        with open(r'/etc/cortx/message_bus.conf.sample', 'w+') as file:
            json.dump({}, file, indent=2)
        Conf.load('index', 'json:///etc/cortx/message_bus.conf.sample')
        Conf.set('index', 'message_broker>type', 'kafka')
        for i in range(len(message_server_list)):
            Conf.set('index', f'message_broker>cluster[{i}]>server', \
                     message_server_list[i])
            Conf.set('index', f'message_broker>cluster[{i}]>port', port_list[i])
        Conf.set('index', 'message_broker>message_bus',  config)
        Conf.save('index')
        # copy this conf file as message_bus.conf
        try:
            os.rename('/etc/cortx/message_bus.conf.sample', \
                      '/etc/cortx/message_bus.conf')
        except OSError as e:
            raise SetupError(e.errno, "Failed to create \
                /etc/cortx/message_bus.conf %s", e)

    @staticmethod
    def _get_server_info(conf_url_index: str, machine_id: str) -> dict:
        """Reads the ConfStore and derives keys related to Event Message.

        Args:
            conf_url_index (str): Index for loaded conf_url
            machine_id (str): Machine_id

        Returns:
            dict: Server Information
        """
        key_list = [f'server_node>{machine_id}']
        ConfKeysV().validate('exists', conf_url_index, key_list)
        server_info = Conf.get(conf_url_index, key_list[0])
        return server_info

    @staticmethod
    def _copy_cluster_map(conf_url_index: str):
        cluster_data = Conf.get(conf_url_index, 'server_node')
        for _, node_data in cluster_data.items():
            hostname = node_data.get('hostname')
            node_name = node_data.get('name')
            Conf.set('cluster', f'cluster>{node_name}', hostname)
        Conf.save('cluster')

    @staticmethod
    def _create_cluster_config(server_info: dict):
        """ Create the config file required for Event Message """
        for key, value in server_info.items():
            Conf.set('cluster', f'server_node>{key}', value)
        Conf.save('cluster')

    @staticmethod
    def _copy_conf_sample_to_conf():
        if not os.path.exists("/etc/cortx/cluster.conf.sample"):
            with open("/etc/cortx/cluster.conf.sample", "w+") as file:
                json.dump({}, file, indent=2)
        # copy this sample conf file as cluster.conf
        try:
            os.rename('/etc/cortx/cluster.conf.sample', \
                '/etc/cortx/cluster.conf')
        except OSError as e:
            raise SetupError(e.errno, "Failed to create /etc/cortx/cluster.conf\
                %s", e)

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

        # Check required python packages
        utils_path = Utils._get_utils_path()
        with open(f"{utils_path}/conf/python_requirements.txt") as file:
            req_pack = []
            for package in file.readlines():
                pack = package.strip().split('==')
                req_pack.append(f"{pack[0]} ({pack[1]})")
        try:
            with open(f"{utils_path}/conf/python_requirements.ext.txt") as extfile :
                for package in extfile.readlines():
                    pack = package.strip().split('==')
                    req_pack.append(f"{pack[0]} ({pack[1]})")
        except Exception:
            Log.info("Not found: "+f"{utils_path}/conf/python_requirements.ext.txt")

        PkgV().validate(v_type='pip3s', args=req_pack)
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

        # start MessageBus service and check status
        start_cmd = SimpleProcess("systemctl start cortx_message_bus")
        _, start_err, start_rc = start_cmd.run()

        if start_rc != 0:
            raise SetupError(start_rc, "Unable to start MessageBus Service \
                %s", start_err.decode('utf-8'))

        status_cmd = SimpleProcess("systemctl status cortx_message_bus")
        _, status_err, status_rc = status_cmd.run()

        if status_rc != 0:
            raise SetupError(status_rc, "MessageBus Service is either failed \
                inactive. %s", status_err.decode('utf-8'))
        return 0

    @staticmethod
    def config(config_template: str):
        """Performs configurations."""
        # Copy cluster.conf.sample file to /etc/cortx/cluster.conf
        Utils._copy_conf_sample_to_conf()

        # Load required files
        config_template_index = 'cluster_config'
        Conf.load('cluster', 'json:///etc/cortx/cluster.conf')
        Conf.load(config_template_index, config_template)

        # Configure log_dir for utils
        cortx_config_index = 'cortx_config'
        Conf.load(cortx_config_index, 'json:///etc/cortx/cortx.conf', \
            skip_reload=True)
        log_dir = Conf.get(config_template_index, \
            'cortx>common>storage>log')
        if log_dir is not None:
            Conf.set(cortx_config_index, 'log_dir', log_dir)
            Conf.save(cortx_config_index)

        try:
            server_list, port_list, config = \
                MessageBrokerFactory.get_server_list(config_template_index)
        except SetupError:
            Log.error(f"Could not find server information in {config_template}")
            raise SetupError(errno.EINVAL, \
                "Could not find server information in %s", config_template)

        Utils._create_msg_bus_config(server_list, port_list, config)
        # Cluster config
        server_info = \
            Utils._get_server_info(config_template_index, Conf.machine_id)
        if server_info is None:
            Log.error(f"Could not find server information in {config_template}")
            raise SetupError(errno.EINVAL, "Could not find server " +\
                "information in %s", config_template)
        Utils._create_cluster_config(server_info)

        #set cluster nodename:hostname mapping to cluster.conf
        Utils._copy_cluster_map(config_template_index)
        Utils._configure_rsyslog()
        # temporary fix for a common message bus log file
        # The issue happend when some user other than root:root is trying
        # to write logs in these log dir/files. This needs to be removed soon!
        mb_log_path = Conf.get(cortx_config_index, 'log_dir', '/var/log')
        os.makedirs(f'{mb_log_path}/cortx/utils/message_bus', exist_ok=True)
        os.chmod(f'{mb_log_path}/cortx/utils/message_bus', 0o0777)
        Path(f'{mb_log_path}/cortx/utils/message_bus/message_bus.log').touch( \
            exist_ok=True)
        os.chmod(f'{mb_log_path}/cortx/utils/message_bus/message_bus.log', 0o0666)
        return 0

    @staticmethod
    def test(plan: str):
        """ Perform configuration testing """
        # Runs cortx-py-utils unittests as per test plan
        try:
            Log.info("Validating cortx-py-utils-test rpm")
            PkgV().validate('rpms', ['cortx-py-utils-test'])
            utils_path = Utils._get_utils_path()
            import cortx.utils.test as test_dir
            plan_path = os.path.join(os.path.dirname(test_dir.__file__), \
                'plans/', plan + '.pln')
            Log.info("Running test plan: %s", plan)
            cmd = "%s/bin/run_test -t  %s" %(utils_path, plan_path)
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
    def reset():
        """Remove/Delete all the data/logs that was created by user/testing."""
        try:
            from cortx.utils.message_bus import MessageBusAdmin
            from cortx.utils.message_bus.message_bus_client import MessageProducer
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
        # Clear the logs
        cortx_config_index = 'cortx_config'
        Conf.load(cortx_config_index, 'json:///etc/cortx/cortx.conf', \
            skip_reload=True)
        log_dir = Conf.get(cortx_config_index, 'log_dir')
        utils_log_path = os.path.join(log_dir, 'cortx/utils')
        if os.path.exists(utils_log_path):
            cmd = "find %s -type f -name '*.log' -exec truncate -s 0 {} +" % utils_log_path
            cmd_proc = SimpleProcess(cmd)
            _, stderr, rc = cmd_proc.run()
            if rc != 0:
                raise SetupError(errors.ERR_OP_FAILED, \
                    "Can not reset log files. %s", stderr)
        return 0

    @staticmethod
    def cleanup(pre_factory: bool):
        """Remove/Delete all the data that was created after post install."""
        conf_file = '/etc/cortx/message_bus.conf'
        if os.path.exists(conf_file):
            # delete message_types
            try:
                from cortx.utils.message_bus import MessageBusAdmin
                mb = MessageBusAdmin(admin_id='cleanup')
                message_types_list = mb.list_message_types()
                if message_types_list:
                    mb.deregister_message_type(message_types_list)
            except MessageBusError as e:
                raise SetupError(e.rc, "Can not cleanup Message Bus. %s", e)
            except Exception as e:
                raise SetupError(errors.ERR_OP_FAILED, "Can not cleanup Message  \
                    Bus. %s", e)

        config_files = ['/etc/cortx/message_bus.conf', \
            '/etc/cortx/cluster.conf']
        Utils._delete_files(config_files)

        if pre_factory:
            # deleting all log files as part of pre-factory cleanup
            cortx_config_index = 'cortx_config'
            Conf.load(cortx_config_index, 'json:///etc/cortx/cortx.conf', \
                skip_reload=True)
            log_dir = Conf.get(cortx_config_index, 'log_dir')
            utils_log_path = os.path.join(log_dir, 'cortx/utils')
            cortx_utils_log_regex = f'{utils_log_path}/**/*.log'
            log_files = glob.glob(cortx_utils_log_regex, recursive=True)
            Utils._delete_files(log_files)

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
