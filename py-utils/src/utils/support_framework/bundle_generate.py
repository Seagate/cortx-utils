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
import threading
import shutil
from datetime import datetime
from typing import List
from cortx.utils.schema.payload import Yaml, Tar
from cortx.utils.support_framework import const
from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.log import Log

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
        message = (f"{const.SUPPORT_BUNDLE_TAG}|{bundle_id}|{node_name}|\
            {comment}|{result}|{msg}")
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
            ComponentsBundle._publish_log(f"Permission denied for creating \
                summary file {e}", ERROR, bundle_id, node_name, comment)
            return None
        except Exception as e:
            ComponentsBundle._publish_log(f'{e}', ERROR, bundle_id, node_name, \
                comment)
            return None
        Log.debug("Summary file created")

    @staticmethod
    def _exc_components_cmd(commands: List, bundle_id: str, path: str, \
            component: str, node_name: str, comment: str):
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
            Log.info(f"Executing command -> {command} {bundle_id} {path}")
            cmd_proc = SimpleProcess(f"{command} {bundle_id} {path}")
            output, err, return_code = cmd_proc.run()
            Log.debug(f"Command Output -> {output} {err}, {return_code}")
            if return_code != 0:
                Log.error(f"Command Output -> {output} {err}, {return_code}")
                ComponentsBundle._publish_log(
                    f"Bundle generation failed for '{component}'", ERROR,
                    bundle_id, node_name, comment)
            else:
                ComponentsBundle._publish_log(
                    f"Bundle generation started for '{component}'", INFO,
                    bundle_id, node_name, comment)

    @staticmethod
    async def init(command: List):
        """
        Initializes the Process of Support Bundle Generation for Every Component.

        command:        cli Command Object :type: command
        return:         None
        """
        bundle_id = command.options.get(const.SB_BUNDLE_ID, '')
        node_name = command.options.get(const.SB_NODE_NAME, '')
        comment = command.options.get(const.SB_COMMENT, '')
        components = command.options.get(const.SB_COMPONENTS, [])

        Log.debug((f"{const.SB_BUNDLE_ID}: {bundle_id}, {const.SB_NODE_NAME}: "
            f"{node_name}, {const.SB_COMMENT}: {comment}, "
            f"{const.SB_COMPONENTS}: {components}, {const.SOS_COMP}"))
        # Read Commands.Yaml and Check's If It Exists.
        cmd_setup_file = os.path.join(Conf.get('cortx_config', 'install_path'),\
            'cortx/utils/conf/support.yaml')
        support_bundle_config = Yaml(cmd_setup_file).load()
        if not support_bundle_config:
            ComponentsBundle._publish_log(f"No such file {cmd_setup_file}", \
                ERROR, bundle_id, node_name, comment)
            return None
        # Path Location for creating Support Bundle.
        path = os.path.join(Conf.get('cortx_config', \
            'support>support_bundle_path'))

        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except PermissionError:
                Log.warn(f"Incorrect permissions for path:{path}")

        bundle_path = os.path.join(path, bundle_id)
        os.makedirs(bundle_path)
        # Start Execution for each Component Command.
        threads = []
        command_files_info = support_bundle_config.get('COMPONENTS')
        # OS Logs are specifically generated hence here Even
        # When All is Selected O.S. Logs Will Be Skipped.
        if components:
            if 'all' not in components:
                components_list = list(set(command_files_info.keys()\
                    ).intersection(set(components)))
            else:
                components_list = list(command_files_info.keys())
                components_list.remove(const.SOS_COMP)
        Log.debug(
            f"Generating for {const.SB_COMPONENTS} {' '.join(components_list)}")
        for each_component in components_list:
            components_commands = []
            components_files = command_files_info[each_component]
            for file_path in components_files:
                file_data = Yaml(file_path).load()
                if file_data:
                    components_commands = file_data.get(
                        const.SUPPORT_BUNDLE.lower(), [])
                if components_commands:
                    thread_obj = threading.Thread(\
                        ComponentsBundle._exc_components_cmd(\
                        components_commands, bundle_id, f"{bundle_path}{os.sep}"\
                        , each_component, node_name, comment))
                    thread_obj.start()
                    Log.debug(f"Started thread -> {thread_obj.ident} " \
                        f"Component -> {each_component}")
                    threads.append(thread_obj)
        directory_path = Conf.get('cortx_config', 'support>support_bundle_path')
        tar_file_name = os.path.join(directory_path, \
            f'{bundle_id}_{node_name}.tar.gz')

        ComponentsBundle._create_summary_file(bundle_id, node_name, \
            comment, bundle_path)

        symlink_path = const.SYMLINK_PATH
        if os.path.exists(symlink_path):
            try:
                shutil.rmtree(symlink_path)
            except PermissionError:
                Log.warn(const.PERMISSION_ERROR_MSG.format(path=symlink_path))
        os.makedirs(symlink_path, exist_ok=True)

        # Wait Until all the Threads Execution is not Complete.
        for each_thread in threads:
            Log.debug(
                f"Waiting for thread - {each_thread.ident} to complete process")
            each_thread.join(timeout=1800)
        try:
            Log.debug(f"Generating tar.gz file on path {tar_file_name} "
                f"from {bundle_path}")
            Tar(tar_file_name).dump([bundle_path])
        except Exception as e:
            ComponentsBundle._publish_log(f"Could not generate tar file {e}", \
                ERROR, bundle_id, node_name, comment)
            return None
        try:
            Log.debug("Create soft-link for generated tar.")
            os.symlink(tar_file_name, os.path.join(symlink_path, \
                f"{const.SUPPORT_BUNDLE}.{bundle_id}"))
            ComponentsBundle._publish_log(f"Tar file linked at location - " \
                f"{symlink_path}", INFO, bundle_id, node_name, comment)
        except Exception as e:
            ComponentsBundle._publish_log(f"Linking failed {e}", ERROR, \
                bundle_id, node_name, comment)
        finally:
            if os.path.isdir(bundle_path):
                shutil.rmtree(bundle_path)
        msg = "Support bundle generation completed."
        ComponentsBundle._publish_log(msg, INFO, bundle_id, node_name, comment)