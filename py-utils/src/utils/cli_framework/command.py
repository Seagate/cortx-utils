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


import json
from typing import Dict, Any
from dict2xml import dict2xml
from prettytable import PrettyTable
from cortx.utils.cli_framework import const

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
            output_type=self._options.get("format","success"))


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
        if self.rc not in  (200, 201, const.OPERATION_SUCESSFUL) :
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
    def dump_success(output: Any, **kwargs) -> str:
        """
        Accepts String as Output and Returns the Same.
        :param output: Output String
        :return: str
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
