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

import argparse
import sys
from cortx.utils.cli_framework import const
from copy import deepcopy
from importlib import import_module
from cortx.utils.cli_framework.command import Command
from typing import Dict, Any
from cortx.utils.cli_framework.arg_validator import *


class ArgumentParser(argparse.ArgumentParser):
    """Overwritten ArgumentParser class for internal purposes"""

    def error(self, message):
        # todo:  Need to Modify the changes for Fetching Error Messages from config file
        self.print_usage(sys.stderr)
        self.exit(2, f'Error: {message.capitalize()}\n')


class CommandParser:
    """
    This Class Parses the Commands from the dictionary object
    """

    def __init__(self, cmd_data: Dict, permissions: Dict):
        self.command = cmd_data
        self.permissions = permissions
        self._communication_obj = {}

    def _handle_main_parse(self, subparsers):
        """
        This Function Handles the Parsing of Single-Level and Multi-Level
        Command Arguments
        :param subparsers: argparser Object
        :return:
        """
        if "sub_commands" in self.command:
            self._handle_subparsers(subparsers, self.command,
                                   self.command["name"])
        elif "args" in self.command:
            self._add_args(self.command, subparsers, self.command["name"])

    def _handle_subparsers(self, sub_parser, data: Dict, name, add_parser_flag=True):
        """
        This Function will handle multiple sub-parsing commands
        :param sub_parser: Arg-parser Object
        :param data: Data for parsing the commands :type: Dict
        :param name: Name of the Command :type:Str
        :param add_parser_flag: Parser Flag Decides whether an new
            parser is object is required or not.:type:Bool
        :return: None
        """
        if add_parser_flag:
             sub_parser = sub_parser.add_parser(data["name"],
                        help=data["description"])
        parser = sub_parser.add_subparsers()
        for each_data in data["sub_commands"]:
            self._add_args(each_data, parser, name)

    def _check_permissions(self, sub_command):
        """
        filter sub_command if found any permissions tag
        if no permissions tag is found it returns true
        """
        allowed = False
        permission_tag =  sub_command.get(const.SUB_COMMANDS_PERMISSIONS, False)
        if permission_tag and self.permissions.get(permission_tag, False):
            allowed = True
        return allowed

    def _handle_comm(self, each_args):
        """
        This method will handle the rest params and create the necessary object.
        :param each_args:
        :return:
        """
        if each_args.get("params", False):
            each_args.pop("params")
            self._communication_obj["params"][
                each_args.get("dest", None) or each_args.get("flag")] = ""
        if each_args.get("json", False):
            each_args.pop("json")
            self._communication_obj["json"][
                each_args.get("dest", None) or each_args.get("flag")] = ""

    def _add_args(self, sub_command: Dict, parser: Any, name):
        """
        This Function will add the cmd_args from the Json to the structure.
        :param sub_command: Action for which the command needs to be added
        :type: str
        :param parser: ArgParse Parser Object :type: Any
        :param name: Name of the Command :type: str
        :return: None
        """
        if not self._check_permissions(sub_command):
            return None
        sub_parser = parser.add_parser(sub_command["name"],
                                       help=sub_command["description"])
        # Check if the command has any arguments.
        if "args" in sub_command:
            self._communication_obj.update(sub_command["comm"])
            self._communication_obj["params"] = {}
            self._communication_obj["json"] = {}
            for each_args in sub_command["args"]:
                if each_args.get("type", None):
                    if each_args.get("type_method"):
                        type_method = each_args.pop("type_method")
                        if each_args.get("type_target"):
                            module_obj = import_module(each_args.pop("type_target"))
                            each_args["type"] = eval(f"module_obj.{type_method}")
                    else:
                        each_args["type"] = eval(each_args["type"])
                if each_args.get("suppress_help", False):
                    each_args.pop("suppress_help")
                    each_args["help"] = argparse.SUPPRESS
                self._handle_comm(each_args)
                flag = each_args.pop("flag")
                sub_parser.add_argument(flag, **each_args)
            sub_parser.set_defaults(command=Command,
                                    action=deepcopy(name),
                                    comm=deepcopy(self._communication_obj),
                                    output=deepcopy(sub_command.get("output", {})),
                                    need_confirmation=sub_command.get("need_confirmation", False),
                                    sub_command_name=sub_command.get("name"))

        # Check if the command has any Commands.
        elif "sub_commands" in sub_command:
            self._handle_subparsers(sub_parser, sub_command, name, False)
