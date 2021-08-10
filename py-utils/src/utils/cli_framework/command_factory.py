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

import sys
import os
from cortx.utils.schema.payload import Json
from cortx.utils.cli_framework import const
from cortx.utils.cli_framework.parser import ArgumentParser, CommandParser


class CommandFactory(object):
    """
    Factory for representing and creating command objects using
    a generic skeleton.
    """

    @staticmethod
    def get_command(argv, permissions={}, component_cmd_dir="", excluded_cmds=[], hidden_cmds=[]):
        """
        Parse the command line as per the syntax and retuns
        returns command representing the command line.
        """
        if len(argv) <= 1:
            argv.append("-h")

        commands_files = os.listdir(component_cmd_dir)
        excluded_cmds.extend(const.EXCLUDED_COMMANDS)

        commands = [command.split(".json")[0] for command in commands_files
                    if command.split(".json")[0] not in excluded_cmds]
        if permissions:
            # common commands both in commands and permissions key list
            commands = [command for command in commands if command in permissions.keys()]
        parser = ArgumentParser(description="Cortx cli commands")
        hidden_cmds.extend(const.HIDDEN_COMMANDS)
        metavar = set(commands).difference(set(hidden_cmds))
        subparsers = parser.add_subparsers(metavar=metavar)

        if  argv[0] in commands:
            # get command json file and filter only allowed first level sub_command
            # create filter_permission_json
            cmd_from_file = Json(os.path.join(component_cmd_dir, f"{argv[0]}.json")).load()
            cmd_obj = CommandParser(cmd_from_file, permissions.get(argv[0], {}))
            cmd_obj._handle_main_parse(subparsers)
        namespace = parser.parse_args(argv)

        sys_module = sys.modules[__name__]
        for attr in ["command", "action", "args"]:
            setattr(sys_module, attr, getattr(namespace, attr))
            delattr(namespace, attr)
        return command(action, vars(namespace), args)
