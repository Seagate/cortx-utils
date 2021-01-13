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

import errno
import argparse
from argparse import RawTextHelpFormatter
from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfStoreError


def main():
    common_parser = argparse.ArgumentParser(description='Conf',
        formatter_class=RawTextHelpFormatter)

    common_parser.add_argument("url",
                               help="representing the Backend for conf store")
    sub_parser = common_parser.add_subparsers(title="command",
        help="represents the action from: set, get, delete\n\n",
        dest='subparser_name')

    # Get argument
    sub_parser_get = sub_parser.add_parser('get', help="This command retrieves"
        " the values for the keys in the \nargument.\n\nOne or more Key(s). "
        "Multiple keys are separated using ';'\nExample(s): k1”, “k1>k2;k3”,"
        " “k4[2]>k5”, “k6>k4[2]>k5\n\nExample command:# conf "
        "json:///tmp/csm.conf get “k6>k4[2]>k5”")
    sub_parser_get.add_argument("kv_list", help="One or more Key(s). "
        "Multiple keys are separated using ';'\nExample(s): k1”, “k1>k2;k3”,"
        " “k4[2]>k5”, “k6>k4[2]>k5”\n\nExample command:# conf "
        "json:///tmp/csm.conf get “k6>k4[2]>k5”\n\n")

    # Set argument
    sub_parser_set = sub_parser.add_parser('set', help="This command adds the "
        "keys and specified values to the conf \nstore. If the key exists, then"
        " old value is overwritten.\n\nOne or more Key Value pair in “key=val”"
        " format.\nMultiple key value pairs are separated using “;” \nExamples:"
        " \n“k1=v1”, “k1=v1;k2=v2”, “k4[2]>k5=v6”, “k6>k4[2]>k5=v3”\n\n"
        "Example command:# conf json:///tmp/csm.conf set “k1>k2='v1';k3=1”\n\n")
    sub_parser_set.add_argument("kv_spec", help="One or more Key Value pair in"
        " “key=val” format.\nMultiple key value pairs are separated using “;” "
        "\nExamples:\n“k1=v1”, “k1=v1;k2=v2”, “k4[2]>k5=v6”, “k6>k4[2]>k5=v3”"
        "\n\nExample command:# conf json:///tmp/csm.conf set “k1>k2='v1';k3=1”"
        "\n\n")

    # Delete argument
    sub_parser_set = sub_parser.add_parser('delete', help="This command deletes"
        " the keys mentioned in the arguments \n(and the associated values) "
        "from the conf store.\n\nOne or more Key(s). Multiple keys are "
        "separated using ';'\nExample(s): “k1”, “k1>k2;k3”, “k4[2]>k5”,"
        " “k6>k4[2]>k5”\n\nExample command:# conf json:///tmp/csm.conf delete "
        "“k1>k2;k3”")
    sub_parser_set.add_argument("kv_list", help="One or more Key(s). Multiple "
        "keys are separated using ';'\nExample(s): “k1”, “k1>k2;k3”, "
        "“k4[2]>k5”, “k6>k4[2]>k5”\n\nExample command:# conf "
        "json:///tmp/csm.conf delete “k1>k2;k3”")

    args = common_parser.parse_args()
    command = args.subparser_name
    index = "conf_cli"
    Conf.load(index, args.url)

    if command == "set":
        key_val = args.kv_spec
    else:
        key_val = args.kv_list

    key_val_lst = key_val.split(';')

    if command == "set":
        key_val_dict = {}
        for each in key_val_lst:
            if len(each.split('=')) > 1:
                key_val_dict[each.split('=')[0]] = eval(each.split('=')[1])
            else:
                raise ConfStoreError(errno.EINVAL,
                    "key or values should not be empty %s", each)
        for key, value in key_val_dict.items():
            Conf.set(index, key, value)
        Conf.save(index)

    elif command == "get":
        for key in key_val_lst:
            vals = Conf.get(index, key)
            print(vals)

    elif command == "delete":
        for key in key_val_lst:
            Conf.delete(index, key)
        Conf.save(index)


if __name__ == "__main__":
    main()
