# CORTX-CSM: CORTX Management web and CLI interface.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
from typing import Dict, List
from csm.common import comm
from csm.common.payload import Yaml, Tar
from csm.core.blogic import const
from datetime import datetime
from csm.common.process import SimpleProcess
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.log import Log

ERROR = "error"
INFO = "info"

class ComponentsBundle:
    """
    This class handles generation for support bundles for different components.
    """
    @staticmethod
    def publish_log(msg, level, bundle_id, node_name, comment):
        """
        Format and Publish Log to ElasticSearch via Rsyslog.
        :param msg: Message to Be added :type: str.
        :param bundle_id: Unique Bundle Id for the Bundle :type:str.
        :param level: Level for the Log. :type: Log.ERROR/LOG.INFO.
        :param node_name: Name of the Node where this is running :type:str.
        :param comment: Comment Added by user to Generate the Bundle :type:str.
        :return: None.
        """
        #Initilize Logger for Uploading the Final Comment to ElasticSearch.
        Log.init("support_bundle",
                 syslog_server=Conf.get(const.CSM_GLOBAL_INDEX, "Log>syslog_server"),
                 syslog_port=int(Conf.get(const.CSM_GLOBAL_INDEX, "Log>syslog_port")),
                 backup_count=Conf.get(const.CSM_GLOBAL_INDEX, "Log>total_files"),
                 file_size_in_mb=Conf.get(const.CSM_GLOBAL_INDEX,
                                          "Log>file_size"),
                 log_path=Conf.get(const.CSM_GLOBAL_INDEX, "Log>log_path"),
                 level=Conf.get(const.CSM_GLOBAL_INDEX, "Log>log_level"))
        result = "Success"
        if level == ERROR:
            result = ERROR.capitalize()
        message = (f"{const.SUPPORT_BUNDLE_TAG}|{bundle_id}|{node_name}|{comment}|"
                   f"{result}|{msg}")
        Log.support_bundle(message)

    @staticmethod
    def exc_components_cmd(commands: List, bundle_id: str, path: str,
            component: str, node_name: str, comment: str):
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
            Log.debug(f"Executing command -> {command} {bundle_id} {path}")
            cmd_proc = SimpleProcess(f"{command} {bundle_id} {path}")
            output, err, return_code = cmd_proc.run()
            Log.debug(f"Command Output -> {output} {err}, {return_code}")
            if return_code != 0:
                Log.error(f"Command Output -> {output} {err}, {return_code}")
                ComponentsBundle.publish_log(
                    f"Bundle generation failed for {component}", ERROR,
                    bundle_id, node_name, comment)


    @staticmethod
    def send_file(protocol_details: Dict, file_path: str):
        """
        Method to send the tar files ove FTP Location.
        :param protocol_details: Dictionary of FTP Details. :type:dict
        :param file_path: Path of tar file to be sent. :type:str
        :return:
        """
        if not protocol_details.get("host", None):
            Log.warn("Skipping file upload as host is not configured.")
            return False
        url = protocol_details.get('url')
        protocol = url.split("://")[0]
        channel = f"{protocol.upper()}Channel"
        if hasattr(comm, channel):
            try:
                channel_obj = getattr(comm, channel)(**protocol_details)
                channel_obj.connect()
            except Exception as e:
                Log.error(f"File connection failed. {e}")
                raise Exception((f"Failed to connect to {protocol}, "
                                 f"please check credentials."))
            try:
                channel_obj.send_file(file_path, protocol_details.get('remote_file'))
            except Exception as e:
                Log.error(f"File upload failed. {e}")
                raise Exception(f"Could not upload the file to {protocol}.")
            finally:
                channel_obj.disconnect()
        else:
            Log.error("Invalid url in csm.conf.")
            raise Exception(f"{protocol} is Invalid.")
        return True

    @staticmethod
    async def init(command: List):
        """
        Initializes the Process of Support Bundle Generation for Every Component.
        :param command: Csm_cli Command Object :type: command
        :return:
        """
        # Fetch Command Arguments.
        bundle_id = command.options.get(const.SB_BUNDLE_ID, "")
        node_name = command.options.get(const.SB_NODE_NAME, "")
        comment = command.options.get(const.SB_COMMENT, "")
        components = command.options.get(const.SB_COMPONENTS, [])
        ftp_msg, file_link_msg, components_list = "", "", []

        Log.debug((f"{const.SB_BUNDLE_ID}: {bundle_id}, {const.SB_NODE_NAME}: {node_name}, "
                   f" {const.SB_COMMENT}: {comment}, {const.SB_COMPONENTS}: {components},"
                   f" {const.SOS_COMP}"))
        # Read Commands.Yaml and Check's If It Exists.
        support_bundle_config = Yaml(const.COMMANDS_FILE).load()
        if not support_bundle_config:
            ComponentsBundle.publish_log(f"No such file {const.COMMANDS_FILE}",
                                         ERROR, bundle_id, node_name, comment)
            return None
        # Path Location for creating Support Bundle.
        path = os.path.join(Conf.get(const.CSM_GLOBAL_INDEX,
                                     f"{const.SUPPORT_BUNDLE}>{const.SB_BUNDLE_PATH}"))
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except PermissionError:
                Log.warn(const.PERMISSION_ERROR_MSG.format(path=path))

        bundle_path = os.path.join(path, bundle_id)
        os.makedirs(bundle_path)
        # Start Execution for each Component Command.
        threads = []
        command_files_info = support_bundle_config.get("COMMANDS")
        # OS Logs are specifically generated hence here Even When All is Selected O.S. Logs Will Be Skipped.
        if components:
            if "all" not in components:
                components_list = list(set(command_files_info.keys()).intersection(set(components)))
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
                    components_commands = file_data.get(const.SUPPORT_BUNDLE.lower(), [])
                if components_commands:
                    thread_obj = threading.Thread(
                        ComponentsBundle.exc_components_cmd(components_commands,
                            bundle_id, f"{bundle_path}{os.sep}", each_component,
                            node_name, comment))
                    thread_obj.start()
                    Log.debug(f"Started thread -> {thread_obj.ident}  Component -> {each_component}")
                    threads.append(thread_obj)
        directory_path = Conf.get(const.CSM_GLOBAL_INDEX,
                                  f"{const.SUPPORT_BUNDLE}>{const.SB_BUNDLE_PATH}")
        tar_file_name = os.path.join(directory_path,
                                     f"{bundle_id}_{node_name}.tar.gz")
        # Create Summary File for Tar.
        summary_file_path = os.path.join(bundle_path, "summary.yaml")
        Log.debug(f"Adding summary file at {summary_file_path}")
        summary_data = {
            const.SB_BUNDLE_ID: str(bundle_id),
            const.SB_NODE_NAME: str(node_name),
            const.SB_COMMENT: repr(comment),
            "Generated Time": str(datetime.isoformat(datetime.now()))
        }
        try:
            Yaml(summary_file_path).dump(summary_data)
        except PermissionError as e:
            ComponentsBundle.publish_log(f"Permission denied for creating summary file {e}",
                                         ERROR, bundle_id, node_name, comment)
            return None
        except Exception as e:
            ComponentsBundle.publish_log(f"{e}", ERROR, bundle_id, node_name,
                comment)
            return None

        Log.debug(f'Summary file created')
        symlink_path = Conf.get(const.CSM_GLOBAL_INDEX,
            f"{const.SUPPORT_BUNDLE}>{const.SB_SYMLINK_PATH}")
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
            ComponentsBundle.publish_log(f"Could not generate tar file {e}", ERROR, bundle_id,
                                         node_name, comment)
            return None
        try:
            Log.debug("Create soft-link for generated tar.")
            os.symlink(tar_file_name, os.path.join(symlink_path,
                                                   f"{const.SUPPORT_BUNDLE}.{bundle_id}"))
            ComponentsBundle.publish_log(f"Tar file linked at location - {symlink_path}", INFO, bundle_id, node_name,
                                         comment)
        except Exception as e:
            ComponentsBundle.publish_log(f"Linking failed {e}", ERROR, bundle_id,
                                         node_name, comment)
        finally:
            if os.path.isdir(bundle_path):
                shutil.rmtree(bundle_path)
        msg = f"Support bundle generation completed."
        ComponentsBundle.publish_log(msg, INFO, bundle_id, node_name, comment)
