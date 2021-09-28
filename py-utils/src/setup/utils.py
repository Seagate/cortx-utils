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
from cortx.utils.common import CortxConf

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

    @staticmethod
    def _get_utils_path() -> str:
        """ Gets install path from cortx.conf and returns utils path """
        install_path = CortxConf.get_key(key='install_path')
        if not install_path:
            error_msg = f"install_path not found in {const.CORTX_CONF_FILE}"
            raise SetupError(errno.EINVAL, error_msg)

    def _set_to_conf_file(key, value):
        """ Add key value pair to cortx.conf file """
        CortxConf.set_key(key, value)
        CortxConf.save()

    # Utils private methods
    @staticmethod
    def _get_from_conf_file(key) -> str:
        """ Fetch and return value for the key from cortx.conf file """
        val = CortxConf.get_key(key=key)

        if not val:
            error_msg = f"Value for key: {key}, not found in {const.CORTX_CONF_FILE}"
            raise SetupError(errno.EINVAL, error_msg)

        return val

    @staticmethod
    def _create_msg_bus_config(message_server_list: list, port_list: list, \
        config: dict):
        """ Create the config file required for message bus """
        mb_index = 'mb_index'
        with open(r'/etc/cortx/utils/message_bus.conf.sample', 'w+') as file:
            json.dump({}, file, indent=2)
        Conf.load(mb_index, 'json:///etc/cortx/utils/message_bus.conf.sample')
        Conf.set(mb_index, 'message_broker>type', 'kafka')
        for i in range(len(message_server_list)):
            Conf.set(mb_index, f'message_broker>cluster[{i}]>server', \
                     message_server_list[i])
            Conf.set(mb_index, f'message_broker>cluster[{i}]>port', port_list[i])
        Conf.set(mb_index, 'message_broker>message_bus',  config)
        Conf.save(mb_index)

        # copy this conf file as message_bus.conf
        try:
            os.rename('/etc/cortx/utils/message_bus.conf.sample', \
                      '/etc/cortx/utils/message_bus.conf')
        except OSError as e:
            raise SetupError(e.errno, "Failed to create \
                /etc/cortx/utils/message_bus.conf %s", e)

    @staticmethod
    def _get_server_info(conf_url_index: str, machine_id: str) -> dict:
        """Reads the ConfStore and derives keys related to Event Message.

        Args:
            conf_url_index (str): Index for loaded conf_url
            machine_id (str): Machine_id

        Returns:
            dict: Server Information
        """
        key_list = [f'node>{machine_id}']
        ConfKeysV().validate('exists', conf_url_index, key_list)
        server_info = Conf.get(conf_url_index, key_list[0])
        return server_info

    @staticmethod
    def _copy_cluster_map(conf_url_index: str):
        Conf.load('cluster', 'yaml:///etc/cortx/cluster.conf', skip_reload=True)
        cluster_data = Conf.get(conf_url_index, 'node')
        for _, node_data in cluster_data.items():
            hostname = node_data.get('hostname')
            node_name = node_data.get('name')
            Conf.set('cluster', f'cluster>{node_name}', hostname)
        Conf.save('cluster')

    @staticmethod
    def _create_iem_config(server_info: dict, machine_id: str):
        """ Create the config file required for Event Message """
        iem_index = 'iem'
        with open('/etc/cortx/utils/iem.conf.sample', 'w+') as file:
            json.dump({}, file, indent=2)
        for _id in ['site_id', 'rack_id']:
            if _id not in server_info.keys():
                server_info[_id] = 1
        Conf.load(iem_index, 'json:///etc/cortx/utils/iem.conf.sample', \
            skip_reload=True)
        Conf.set(iem_index, f'node>{machine_id}>cluster_id', \
            server_info['cluster_id'])
        Conf.set(iem_index, f'node>{machine_id}>site_id', server_info['site_id'])
        Conf.set(iem_index, f'node>{machine_id}>rack_id', server_info['rack_id'])
        Conf.save(iem_index)

        # copy this sample conf file as iem.conf
        try:
            os.rename('/etc/cortx/utils/iem.conf.sample', \
                '/etc/cortx/utils/iem.conf')
        except OSError as e:
            raise SetupError(e.errno, "Failed to create /etc/cortx/utils/iem.conf\
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
    def post_install(post_install_template: str):
        """ Performs post install operations """

        # Check required python packages
        install_path = Utils._get_from_conf_file('install_path')
        utils_path = install_path + '/cortx/utils'
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
        default_sb_path = '/var/log/cortx/support_bundle'
        Utils._set_to_conf_file('support>local_path', default_sb_path)
        os.makedirs(default_sb_path, exist_ok=True)

        post_install_template_index = 'post_install_index'
        Conf.load(post_install_template_index, post_install_template)

        machine_id = Conf.machine_id
        key_list = [f'node>{machine_id}>hostname', f'node>{machine_id}>name']
        ConfKeysV().validate('exists', post_install_template_index, key_list)

        #set cluster nodename:hostname mapping to cluster.conf (needed for Support Bundle)
        Utils._copy_cluster_map(post_install_template_index)

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
    def config(config_template: str):
        """Performs configurations."""
        # Create directory for utils configurations
        config_dir = '/etc/cortx/utils'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # Load required files
        config_template_index = 'config'
        Conf.load(config_template_index, config_template)
        # Configure log_dir for utils
        log_dir = Conf.get(config_template_index, \
            'cortx>common>storage>log')
        if log_dir is not None:
            CortxConf.set_key('log_dir', log_dir)
            CortxConf.save()

        # Create message_bus config
        try:
            server_list, port_list, config = \
                MessageBrokerFactory.get_server_list(config_template_index)
        except SetupError:
            Log.error(f"Could not find server information in {config_template}")
            raise SetupError(errno.EINVAL, \
                "Could not find server information in %s", config_template)
        Utils._create_msg_bus_config(server_list, port_list, config)

        # Create iem config
        machine_id = Conf.machine_id
        server_info = Utils._get_server_info(config_template_index, machine_id)
        if server_info is None:
            Log.error(f"Could not find server information in {config_template}")
            raise SetupError(errno.EINVAL, "Could not find server " +\
                "information in %s", config_template)
        Utils._create_iem_config(server_info, machine_id)

        # set cluster nodename:hostname mapping to cluster.conf
        Utils._copy_cluster_map(config_template_index)
        Utils._configure_rsyslog()

        # get shared storage from cluster.conf and set it to cortx.conf
        shared_storage = Conf.get(config_template_index, \
            'cortx>common>storage>shared')
        if shared_storage:
            Utils._set_to_conf_file('support>shared_path', shared_storage)

        # temporary fix for a common message bus log file
        # The issue happend when some user other than root:root is trying
        # to write logs in these log dir/files. This needs to be removed soon!
        log_dir = CortxConf.get_key('log_dir', '/var/log')
        utils_log_dir = CortxConf.get_log_path(base_dir=log_dir)
        #message_bus
        os.makedirs(os.path.join(utils_log_dir, 'message_bus'), exist_ok=True)
        os.chmod(os.path.join(utils_log_dir, 'message_bus'), 0o0777)
        Path(os.path.join(utils_log_dir,'message_bus/message_bus.log')) \
            .touch(exist_ok=True)
        os.chmod(os.path.join(utils_log_dir,'message_bus/message_bus.log'), 0o0666)
        #iem
        os.makedirs(os.path.join(utils_log_dir, 'iem'), exist_ok=True)
        os.chmod(os.path.join(utils_log_dir, 'iem'), 0o0777)
        Path(os.path.join(utils_log_dir, 'iem/iem.log')).touch(exist_ok=True)
        os.chmod(os.path.join(utils_log_dir, 'iem/iem.log'), 0o0666)
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
        import time
        _purge_retry = 20
        try:
            from cortx.utils.message_bus import MessageBusAdmin
            from cortx.utils.message_bus.message_bus_client import MessageProducer
            mb = MessageBusAdmin(admin_id='reset')
            message_types_list = mb.list_message_types()
            if message_types_list:
                for message_type in message_types_list:
                    producer = MessageProducer(producer_id=message_type, \
                        message_type=message_type, method='sync')
                    for retry_count in range(1, (_purge_retry + 2)):
                        if retry_count > _purge_retry:
                            Log.error(f"MessageBusError: {errors.ERR_OP_FAILED} " \
                                f" Unable to delete messages for message type" \
                                f" {message_type} after {retry_count} retries")
                            raise MessageBusError(errors.ERR_OP_FAILED,\
                                "Unable to delete messages for message type" + \
                                "%s after %d retries", message_type, \
                                retry_count)
                        rc = producer.delete()
                        if rc == 0:
                            break
                        time.sleep(2*retry_count)
        except MessageBusError as e:
            raise SetupError(e.rc, "Can not reset Message Bus. %s", e)
        except Exception as e:
            raise SetupError(errors.ERR_OP_FAILED, "Internal error, can not \
                reset Message Bus. %s", e)
        # Clear the logs
        utils_log_path = CortxConf.get_log_path()
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
        conf_file = '/etc/cortx/utils/message_bus.conf'
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

        config_files = ['/etc/cortx/utils/message_bus.conf', \
            '/etc/cortx/utils/iem.conf']
        Utils._delete_files(config_files)

        if pre_factory:
            # deleting all log files as part of pre-factory cleanup
            utils_log_path = CortxConf.get_log_path()
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
