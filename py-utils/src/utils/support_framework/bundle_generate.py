#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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
import shutil
import asyncio
from typing import List
from datetime import datetime

from cortx.utils.log import Log
from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store import MappedConf
from cortx.utils.support_framework import const
from cortx.utils.schema.payload import Yaml, Tar
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.const import CLUSTER_CONF_LOG_KEY, DEFAULT_INSTALL_PATH

ERROR = 'error'
INFO = 'info'


class ComponentsBundle:

    """This class handles generation for support bundles for different components."""

    @staticmethod
    def _publish_log(msg, level, bundle_id, node_name, comment):
        """
        Format and Publish Log to ElasticSearch via Rsyslog.

        msg:            Message to Be added :type: str.
        bundle_id:      Unique Bundle Id for the Bundle :type:str.
        level:          Level for the Log. :type: Log.ERROR/LOG.INFO.
        node_name:      Name of the Node where this is running :type:str.
        comment:        Comment Added by user to Generate the Bundle :type:str.
        return:         None.
        """
        result = 'Success'
        if level == ERROR:
            result = ERROR.capitalize()
        message = (f"{const.SUPPORT_BUNDLE_TAG}|{bundle_id}|{node_name}|" \
            f"{comment}|{result}|{msg}")
        Log.support_bundle(message)

    @staticmethod
    def _create_summary_file(bundle_id, node_name, comment, bundle_path):
        # Create Summary File for Tar.
        summary_file_path = os.path.join(bundle_path, 'summary.yaml')
        Log.info(f"Adding summary file at {summary_file_path}")
        summary_data = {
            const.SB_BUNDLE_ID: str(bundle_id),
            const.SB_NODE_NAME: str(node_name),
            const.SB_COMMENT: repr(comment),
            "Generated Time": str(datetime.isoformat(datetime.now()))
        }
        try:
            Yaml(summary_file_path).dump(summary_data)
        except PermissionError as e:
            Log.error(f"Permission denied for creating " \
                f"summary file {e}")
            Log.error(f"Permission denied for creating " \
                f"summary file {e}", ERROR, bundle_id, node_name, comment)
        except Exception as e:
            Log.error(f"Permission denied for creating " \
                f"summary file {e}")
            Log.error(f'{e}', ERROR, bundle_id, node_name, \
                comment)
        Log.debug("Summary file created")

    @staticmethod
    async def _exc_components_cmd(commands: List, bundle_id: str, path: str, \
            component: str, node_name: str, comment: str, config_url:str,
            services:str, binlogs:bool, coredumps:bool, stacktrace:bool,
            duration:str, size_limit:str):
        """
        Executes the Command for Bundle Generation of Every Component.

        commands:       Command of the component :type:str
        bundle_id:      Unique Bundle ID of the generation process. :type:str
        path:           Path to create the tar by components :type:str
        component:      Name of Component to be executed :type: str
        node_name:      Name of Node where the Command is being Executed :type:str
        comment:        User Comment: type:str
        """
        for command in commands:
        # SB Framework will not parse additional filters until all the components
        # accept filters in their respective support bundle scripts.

        #    Log.info(f"Executing command -> {command} -b {bundle_id} -t {path}"
        #        f" -c {config_url} -s {services} --duration {duration}"
        #        f" --size_limit {size_limit} --binlogs {binlogs}"
        #        f" --coredumps {coredumps} --stacktrace {stacktrace}")

        #    cmd_proc = SimpleProcess(f"{command} -b {bundle_id} -t {path} -c {config_url}"
        #        f" -s {services} --duration {duration} --size_limit {size_limit}"
        #        f" --binlogs {binlogs} --coredumps {coredumps} --stacktrace {stacktrace}")

            Log.info(f"Executing command -> {command} -b {bundle_id} -t {path}"
                f" -c {config_url} -s {services}")

            cmd_proc = SimpleProcess(f"{command} -b {bundle_id} -t {path} -c {config_url}"
                f" -s {services}")
            output, err, return_code = cmd_proc.run()
            Log.debug(f"Command Output -> {output} {err}, {return_code}")
            if return_code != 0:
                Log.error(f"Command Output -> {output} {err}, {return_code}")
            else:
                Log.debug(f"Command Output -> {output} {err}, {return_code}")
            return component, return_code

    @staticmethod
    async def init(bundle_obj, node_id, config_url, **kwargs):
        """
        Initializes the Process of Support Bundle Generation for Every Component.

        command:        cli Command Object :type: command
        return:         None
        """
        cluster_conf = MappedConf(config_url)
        log_path = os.path.join(cluster_conf.get(CLUSTER_CONF_LOG_KEY), \
            f'utils/{Conf.machine_id}/support')
        log_level = cluster_conf.get('utils>log_level', 'INFO')
        Log.init('support_bundle_node', log_path, level=log_level, \
            backup_count=5, file_size_in_mb=5)
        bundle_id = bundle_obj.bundle_id
        node_name = bundle_obj.node_name
        comment = bundle_obj.comment
        components_list = bundle_obj.components
        services_dict = bundle_obj.services
        Log.info(f"components:{components_list}")
        bundle_path = bundle_obj.bundle_path
        duration = kwargs.get('duration')
        size_limit = kwargs.get('size_limit')
        binlogs = kwargs.get('binlogs')
        coredumps = kwargs.get('coredumps')
        stacktrace = kwargs.get('stacktrace')

        Log.debug((f"{const.SB_BUNDLE_ID}: {bundle_id}, {const.SB_NODE_NAME}: "
            f"{node_name}, {const.SB_COMMENT}: {comment}, "
            f"{const.SB_COMPONENTS}: {components_list}, {const.SOS_COMP}"))
        # Read support_bundle.Yaml and Check's If It Exists.
        cmd_setup_file = os.path.join(
            cluster_conf.get('install_path', DEFAULT_INSTALL_PATH),
            const.SUPPORT_YAML)
        try:
            support_bundle_config = Yaml(cmd_setup_file).load()
        except Exception as e:
            Log.error(f"Internal error while parsing YAML file {cmd_setup_file}{e}")
        if not support_bundle_config:
            Log.error(f"No such file {cmd_setup_file}. ERROR:{ERROR}")

        # Start Execution for each Component Command.
        command_files_info = support_bundle_config.get('COMPONENTS')
        # OS Logs are specifically generated hence here Even
        # When All is Selected O.S. Logs Will Be Skipped.
        for each_component in components_list:
            services = services_dict[each_component]
            components_commands = []
            components_files = command_files_info[each_component]
            for file_path in components_files:
                if not os.path.exists(file_path):
                    Log.error(f"'{file_path}' file does not exist!")
                    continue
                try:
                    file_data = Yaml(file_path).load()
                except Exception as e:
                    Log.error(f"Internal error while parsing YAML file {file_path}{e}")
                    file_data = None
                    break
                if file_data:
                    components_commands = file_data.get(
                        const.SUPPORT_BUNDLE.lower(), [])
                else:
                    Log.error(f"Support.yaml file is empty: {file_path}")
                    break
                if components_commands:
                    component, return_code = await(\
                        ComponentsBundle._exc_components_cmd(\
                        components_commands, f'{bundle_id}_{node_id}_{each_component}',
                            f'{bundle_path}{os.sep}', each_component,
                            node_name, comment, config_url, services,
                            binlogs, coredumps, stacktrace, duration,
                            size_limit))
                    if return_code != 0:
                        Log.error(
                            f"Bundle generation failed for component - '{component}'")
                    else:
                        Log.info(
                            f"Bundle generation started for component - '{component}'")
        tar_file_name = os.path.join(bundle_path, \
            f'{bundle_id}_{node_id}.tar.gz')

        ComponentsBundle._create_summary_file(bundle_id, node_name, \
            comment, bundle_path)
        try:
            Log.debug(f"Generating tar.gz file on path {tar_file_name} "
                f"from {bundle_path}")
            Tar(tar_file_name).dump([bundle_path])
            bundle_status = f"Successfully generated SB at path:{bundle_path}"
        except Exception as e:
            bundle_status = f"Failed to generate tar file. ERROR:{e}"
            Log.error(f"Could not generate tar file {e}")
        finally:
            if os.path.exists(bundle_path):
                for each_dir in os.listdir(bundle_path):
                    comp_dir = os.path.join(bundle_path, each_dir)
                    if os.path.isdir(comp_dir):
                        shutil.rmtree(comp_dir)
                if os.path.exists(os.path.join(bundle_path, 'summary.yaml')):
                    os.remove(os.path.join(bundle_path, 'summary.yaml'))

        Log.info("Support bundle generation completed.")
        # Update Status in ConfStor
        Conf.load(const.SB_INDEX, 'json://' + const.FILESTORE_PATH, fail_reload=False)
        Conf.set(const.SB_INDEX, f'{node_id}>{bundle_id}>status', bundle_status)
        Conf.save(const.SB_INDEX)
