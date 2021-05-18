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
import json
from typing import Dict, Any
from copy import deepcopy
from dict2xml import dict2xml
from prettytable import PrettyTable
from importlib import import_module
from cortx.utils.cli import const

class Command:
    """CLI Command Base Class"""

    def __init__(self, name, options, args):
        self._method = options["comm"]["method"]
        self._target = options["comm"]["target"]
        self._comm = options["comm"]
        self._options = options
        self._args = args
        self._name = name
        self._output = options["output"]
        self._need_confirmation = options["need_confirmation"]
        self._sub_command_name = options["sub_command_name"]

    @property
    def name(self):
        return self._name

    @property
    def options(self):
        return self._options

    @property
    def args(self):
        return self._args

    @property
    def method(self):
        return self._method

    @property
    def target(self):
        return self._target

    @property
    def comm(self):
        return self._comm

    @property
    def need_confirmation(self):
        return self._need_confirmation

    @property
    def sub_command_name(self):
        return self._sub_command_name

    def process_response(self, response, out, err):
        """Process Response as per display method in format else normal display"""
        output_obj = Output(self, response)
        return output_obj.dump(out, err, **self._output,
                               output_type=self._options.get("format",
                                                             "success"))

class CommandParser:
    """
    This Class Parses the Commands from the dictionary object
    """

    def __init__(self, cmd_data: Dict, permissions: Dict):
        self.command = cmd_data
        self.permissions = permissions
        self._communication_obj = {}

    def handle_main_parse(self, subparsers):
        """
        This Function Handles the Parsing of Single-Level and Multi-Level
        Command Arguments
        :param subparsers: argparser Object
        :return:
        """
        if "sub_commands" in self.command:
            self.handle_subparsers(subparsers, self.command,
                                   self.command["name"])
        elif "args" in self.command:
            self.add_args(self.command, subparsers, self.command["name"])

    def handle_subparsers(self, sub_parser, data: Dict, name, add_parser_flag=True):
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
            self.add_args(each_data, parser, name)

    def check_permissions(self, sub_command):
        """
        filter sub_command if found any permissions tag
        if no permissions tag is found it returns true
        """
        allowed = False
        permission_tag =  sub_command.get(const.SUB_COMMANDS_PERMISSIONS, False)
        if permission_tag and self.permissions.get(permission_tag, False):
            allowed = True
        return allowed

    def handle_comm(self, each_args):
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

    def add_args(self, sub_command: Dict, parser: Any, name):
        """
        This Function will add the cmd_args from the Json to the structure.
        :param sub_command: Action for which the command needs to be added
        :type: str
        :param parser: ArgParse Parser Object :type: Any
        :param name: Name of the Command :type: str
        :return: None
        """
        if not self.check_permissions(sub_command):
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
                    if each_args.get("type_target"):
                        module_obj = import_module(each_args.pop("type_target"))
                        each_args["type"] = eval(f"module_obj.{each_args['type']}")
                    else:
                        each_args["type"] = eval(each_args["type"])
                if each_args.get("suppress_help", False):
                    each_args.pop("suppress_help")
                    each_args["help"] = argparse.SUPPRESS
                self.handle_comm(each_args)
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
            self.handle_subparsers(sub_parser, sub_command, name, False)

class Output:
    """CLI Response Display Class"""
    def __init__(self, command, response):
        self.command = command
        self.rc = response.rc()
        self.output = response.output()

    def dump(self, out, err, output_type, **kwargs) -> None:
        """Dump the Output on CLI"""
        # Todo: Need to fetch the response messages from a file for localization.
        # TODO: Check 201 response code also for creation requests.
        if self.rc not in  (200, 201, const.CSM_OPERATION_SUCESSFUL) :
            if isinstance(self.output, str):
                errstr = Output.error(self.rc, self.output)
            else:
                errstr = Output.error(self.rc, kwargs.get("error") ,
                                  self.output)
            err.write(f"{errstr}\n" or "")
            return None
        elif output_type:
            output = getattr(Output, f"dump_{output_type}")(self.output,
                                                            **kwargs)
            out.write(f"{output}\n")

    @staticmethod
    def dump_success(output: Any, **kwargs):
        """
        Accepts String as Output and Returns the Same.
        :param output: Output String
        :return:
        """
        return str(kwargs.get("success", output))

    @staticmethod
    def error(rc: int, message: str, stacktrace=None) -> str:
        """Format for Error message"""
        if not stacktrace:
            return f"error({rc}): {message}\n"
        return f"error({rc}): Error:- {stacktrace.get('message')}"

    @staticmethod
    def create_by_row(table_obj, table,data):
        """
        Features Creation of Table By Filling each row data.

        This Works for Data which is in format as follows:
        1) Either the Data is in an array of Dictionaries.
        e.g.
         {
            "filters":[
                    {
                         "key1":"value1",
                         "key2":"value2"
                    },
                    {
                         "key1":"value1",
                         "key2":"value2"
                    }
                ]
         }
        2) The Data is a complete Single Dictionary.
          {
         "key1":"value1",
         "key2":"value2"
         }

        :param table_obj: Pretty Table Object :type:Object
        :param data: data to be displayed in Table :type:dict
        :param table: Table Output From Json :type:dict
        :return:
        """
        table_obj.field_names = table["headers"].values()
        if table.get("filters", False):
            for each_row in data[table["filters"]]:
                table_obj.add_row(
                    [each_row.get(x) for x in table["headers"].keys()])
        else:
            table_obj.add_row([data.get(x) for x in table["headers"].keys()])

    @staticmethod
    def create_by_column(table_obj, table, data):
        """
        Features Creation of Table By Filling each column data.

        This Works for Data which is in format as follows:
        1) For a Response Where the data compromised of multiple Keys and each
         contain list of Options.
        e.g.:
        {
            "key1" : ["Value1", "Value2", ......., "ValueN"],
            "key2" : ["Value1", "Value2", ......., "ValueN"]
        }

        :param table_obj: Pretty Table Object :type:Object
        :param data: data to be displayed in Table :type:dict
        :param table: Table Output From Json :type:dict
        :return:
        """
        # Finds the List which has Max Values.
        max_length_list = max(map(lambda key: len(data[key]), table["headers"].keys()))
        for each_key in table["headers"].keys():
            # Make All the Other Lists to same length to maintain Uniformity for the
            # table displayed on CLI.
            padding_length = max_length_list - len(data[each_key])
            new_data = data[each_key]
            new_data.extend(padding_length * [table.get("padding_element", " ")])
            # Add Padded List to the Column.
            table_obj.add_column(table["headers"][each_key], new_data)

    @staticmethod
    def dump_table(data: Any, table: Dict, **kwargs: Dict) -> str:
        """
        Format for Table Data
        :param data: data to be displayed in Table :type:dict
        :param table: Table Output From Json :type:dict
        :return: Created Table. :type Str
        """
        table_obj = PrettyTable()
        if table.get("create_by_column", False):
            Output.create_by_column(table_obj, table, data)
        else:
            Output.create_by_row(table_obj, table, data)
        return "{0}".format(table_obj)

    @staticmethod
    def dump_xml(data, **kwargs: Dict) -> str:
        """Format for XML Data"""
        return dict2xml(data)

    @staticmethod
    def dump_json(data, **kwargs: Dict) -> str:
        """Format for Json Data"""
        return json.dumps(data, indent=4, sort_keys=True)
