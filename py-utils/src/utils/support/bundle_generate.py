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
from sys import modules
import threading
import shutil
from string import Template
from typing import List
from datetime import datetime

from cortx.utils.schema.payload import Yaml, Tar
from cortx.utils.support import const
from cortx.utils.process import SimpleProcess
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.log import Log

ERROR = "error"
INFO = "info"


class ComponentsBundle:
    """
    This class handles generation for support bundles for different components.
    """
    @staticmethod
    def _publish_log(msg, level, bundle_id, node_name, comment):
        """
        Format and Publish Log to ElasticSearch via Rsyslog.
        :param msg: Message to Be added :type: str.
        :param bundle_id: Unique Bundle Id for the Bundle :type:str.
        :param level: Level for the Log. :type: Log.ERROR/LOG.INFO.
        :param node_name: Name of the Node where this is running :type:str.
        :param comment: Comment Added by user to Generate the Bundle :type:str.
        :return: None.
        """
        result = "Success"
        if level == ERROR:
            result = ERROR.capitalize()
        message = (f"{const.SUPPORT_BUNDLE_TAG}|{bundle_id}|{node_name}|{comment}|{result}|{msg}")
        Log.support_bundle(message)

    @staticmethod
    def _create_summary_file(bundle_id, node_name, comment, bundle_path):
        # Create Summary File for Tar.
        summary_file_path = os.path.join(bundle_path, "summary.yaml")
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
            ComponentsBundle._publish_log(f"Permission denied for creating summary file {e}",
                                         ERROR, bundle_id, node_name, comment)
            return None
        except Exception as e:
            ComponentsBundle._publish_log(f"{e}", ERROR, bundle_id, node_name,
                comment)
            return None
        Log.debug('Summary file created')

    @staticmethod
    def _exc_components_cmd(commands: List, bundle_id: str, path: str,
            component: str, node_name: str, comment: str, modules: str):
        """
        Executes the Command for Bundle Generation of Every Component.
        :param commands: Command of the component :type:str
        :param bundle_id: Unique Bundle ID of the generation process. :type:str
        :param path: Path to create the tar by components :type:str
        :param component: Name of Component to be executed :type: str
        :param node_name:Name of Node where the Command is being Executed
        :type:str
        :param comment: :User Comment: type:str
        :return:
        """
        for command in commands:
            Log.info(f"Executing command -> {command} {bundle_id} {path} {modules}")
            cmd_temp = Template(command)
            command = cmd_temp.substitute(BUNDLE_ID=bundle_id, PATH=path, MODULES=modules)
            cmd_proc = SimpleProcess(command)
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
        :param command: Csm_cli Command Object :type: command
        :return:
        """
        from cortx.utils.shared_storage import Storage
        shared_path = Storage.get_path()
        # Path Location for creating Support Bundle.
        path = os.path.join(shared_path, 'support_bundle')
        # Fetch Command Arguments.
        Log.init('support_bundle',
                syslog_server='localhost',
                syslog_port=514,
                log_path=Conf.get('cortx_conf', 'support>support_bundle_path'),
                level='INFO')
        bundle_id = command.options.get(const.SB_BUNDLE_ID, "")
        node_name = command.options.get(const.SB_NODE_NAME, "")
        comment = command.options.get(const.SB_COMMENT, "")
        components = command.options.get(const.SB_COMPONENTS, [])
        Log.debug((f"{const.SB_BUNDLE_ID}: {bundle_id}, {const.SB_NODE_NAME}: {node_name}, "
                   f" {const.SB_COMMENT}: {comment}, {const.SB_COMPONENTS}: {components},"
                   f" {const.SOS_COMP}"))

        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except PermissionError:
                Log.warn(f"Incorrect permissions for path:{path}")

        bundle_path = os.path.join(path, bundle_id)
        os.makedirs(bundle_path)
        # Start Execution for each Component Command.
        threads = []
        avail_components =  next(os.walk('/opt/seagate/cortx/'))[1]
        # OS Logs are specifically generated hence here Even 
        # When All is Selected O.S. Logs Will Be Skipped.
        cmpt_wo_flt = {}
        if components:
            # segregate components and modules into kv
            for each in components:
                comp_kv = each.split(':', 1)
                cmpt_wo_flt[comp_kv[0]] = comp_kv[1] if len(comp_kv)>1 else ''
            if 'all' not in components:
                components_list = list(set(avail_components).intersection(set(cmpt_wo_flt.keys())))
            else:
                components_list = list(avail_components)
                components_list.remove(const.SOS_COMP)
        Log.debug(
            f"Generating for {const.SB_COMPONENTS} {' '.join(components_list)}")
        for component in components_list:
            components_commands = []
            component_path = os.path.join(Conf.get('cortx_conf',
                'install_path'), f'cortx/{component}/conf/support.yaml')

            if os.path.exists(component_path):
                Conf.load('support_commands', f'yaml://{component_path}', fail_reload=False)
                raw_command = Conf.get('support_commands', f'bundle>create>url')
                cmd_args = Conf.get('support_commands', f'bundle>create>args')
                components_commands.append(f"{raw_command} {cmd_args}")
                if components_commands:
                    modules = cmpt_wo_flt[component]
                    thread_obj = threading.Thread(
                        ComponentsBundle._exc_components_cmd(
                            components_commands, f'{bundle_id}_{component}',
                            f'{bundle_path}{os.sep}', component, node_name,
                            comment, modules))
                    thread_obj.start()
                    Log.debug(f"Started thread -> {thread_obj.ident}  Component -> {component}")
                    threads.append(thread_obj)

        tar_file_name = os.path.join(path,
                                     f'{bundle_id}_{node_name}.tar.gz')

        ComponentsBundle._create_summary_file(bundle_id, node_name, comment, bundle_path)

        symlink_path = const.SYMLINK_PATH
        if os.path.exists(symlink_path):
            try:
                shutil.rmtree(symlink_path)
            except PermissionError:
                Log.warn(const.PERMISSION_ERROR_MSG.format(path = symlink_path))
        os.makedirs(symlink_path, exist_ok = True)

        # Wait Until all the Threads Execution is not Complete.
        for each_thread in threads:
            Log.debug(
                f"Waiting for thread - {each_thread.ident} to complete process")
            each_thread.join(timeout=1800)
        try:
            Log.debug(f"Generating tar.gz file on path {tar_file_name} from {bundle_path}")
            Tar(tar_file_name).dump([bundle_path])
        except Exception as e:
            ComponentsBundle._publish_log(f"Could not generate tar file {e}", ERROR, bundle_id,
                                         node_name, comment)
            return None
        try:
            Log.debug("Create soft-link for generated tar.")
            os.symlink(tar_file_name, os.path.join(symlink_path,
                                                   f'{const.SUPPORT_BUNDLE}.{bundle_id}'))
            ComponentsBundle._publish_log(f"Tar file linked at location - {symlink_path}", INFO, bundle_id, node_name,
                                         comment)
        except Exception as e:
            ComponentsBundle._publish_log(f"Linking failed {e}", ERROR, bundle_id,
                                         node_name, comment)
        finally:
            if os.path.isdir(bundle_path):
                shutil.rmtree(bundle_path)
        msg = "Support bundle generation completed."
        ComponentsBundle._publish_log(msg, INFO, bundle_id, node_name, comment)
