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
import inspect
import sys
import traceback
from argparse import RawTextHelpFormatter
from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError
from cortx.utils.schema import Format


class ConfCli:
    """ CLI for the Conf Store """
    _index = "conf_cli"

    @staticmethod
    def init(url: str):
        """ Load ConfStore URL """
        Conf.load(ConfCli._index, url)

    @staticmethod
    def set(args):
        """ Set Key Value """
        kv_delim = '=' if args.kv_delim == None else args.kv_delim
        if len(kv_delim) > 1 or kv_delim not in [':', '>', '.', '|', '/', '=']:
            raise ConfError(errno.EINVAL, "invalid delim %s", kv_delim)
        kv_list = args.args[0].split(';')
        for kv in kv_list:
            try:
                key, val = kv.split(kv_delim, 1)
            except:
               raise ConfError(errno.EINVAL, "Invalid KV pair %s", kv)
            Conf.set(ConfCli._index, key, val)
        Conf.save(ConfCli._index)

    @staticmethod
    def get(args) -> str:
        """ Obtain value for the given keys """
        params = args.args
        key_list = params[0].split(';')
        n_keys = len(key_list)
        def_val_list = list(None for i in range(0, n_keys))
        if len(params) > 1:
            def_val_list = params[1].split(';')
            if len(def_val_list) != n_keys:
                raise ConfError(errno.EINVAL,
                    "No. of default values, dont match no. of keys")
        val_list = []
        for i in range(0, n_keys):
            val = Conf.get(ConfCli._index, key_list[i], def_val_list[i])
            val_list.append(val)
        format_type = 'json' if args.format == None else args.format
        return Format.dump(val_list, format_type)

    @staticmethod
    def delete(args):
        """ Deletes given set of keys from the config """
        key_list = args.args[0].split(';')
        is_deleted = []
        for key in key_list:
            status = Conf.delete(ConfCli._index, key)
            is_deleted.append(status)
        if any(is_deleted):
            Conf.save(ConfCli._index)

    @staticmethod
    def get_keys(args) -> list:
        """ Returns list of keys present in store """
        key_index = 'true' if args.key_index == None else args.key_index.lower().strip()
        key_index = True if key_index == 'true' else False if key_index == 'false' else None
        if key_index == None:
            raise ConfError(errno.EINVAL, "invalid key_index value %s", key_index)
        return Conf.get_keys(ConfCli._index, key_index=key_index)

    @staticmethod
    def get_kv(args) -> list:
        """ Returns list of keys present in store """
        key_index = 'true' if args.key_index == None else args.key_index.lower().strip()
        key_index = True if key_index == 'true' else False if key_index == 'false' else None
        if key_index == None:
            raise ConfError(errno.EINVAL, "invalid key_index value %s", key_index)
        return Conf.get_kv(ConfCli._index, key_index=key_index)


class GetCmd:
    """ Get Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('get', help=
            "Retrieves the values for one or more keys\n."
            "Multiple keys are separated using ';'.\n"
            "Example(s): 'k1', 'k1>k2;k3', 'k4[2]>k5', 'k6>k4[2]>k5'\n\n"
            "Example command:\n"
            "# conf json:///tmp/csm.conf get 'k6>k4[2]>k5'\n\n")
        s_parser.set_defaults(func=ConfCli.get)
        s_parser.add_argument('-f', dest='format', help=
                'Output Format json(default), yaml or toml')
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class SetCmd:
    """ Set Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('set', help=
            "This command adds the keys and specified values to the conf\n"
            "store. If the key exists, then old value is overwritten.\n\n"
            "One or more Key Value pair as 'key=val' format.\n"
            "Multiple key value pairs are separated using “;” \n"
            "Examples: 'k1=v1', 'k1=v1;k2=v2', 'k4[2]>k5=v6', 'k6>k4[2]>k5=v3'\n\n"
            "Example command:\n"
            "# conf json:///tmp/csm.conf set 'k1>k2=v1;k3=1'\n\n")
        s_parser.set_defaults(func=ConfCli.set)
        s_parser.add_argument('-d', dest='kv_delim',
            help="Delimiter for k=v (default is '=')")
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class DeleteCmd:
    """ Delete Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('delete', help=
            "This command deletes the keys mentioned in the arguments\n"
            "(and the associated values) from the conf store.\n\n"
            "One or more Key(s). Multiple keys are separated using ';'\n"
            "Example(s): 'k1', 'k1>k2;k3', 'k4[2]>k5', 'k6>k4[2]>k5'\n\n"
            "Example command:\n"
            "# conf json:///tmp/csm.conf delete 'k1>k2;k3'\n\n")
        s_parser.set_defaults(func=ConfCli.delete)
        s_parser.add_argument('args', nargs='+', default=[], help='args')

class GetsKeysCmd:
    """ Get keys command structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('get_keys', help=
            "Retrieves the list of keys\n."
            "Example(s): ['k1', 'k1>k2','k3'], ['k4[2]>k5', 'k6>k4[2]>k5']\n\n"
            "Example command:\n"
            "# conf json:///tmp/csm.conf get_keys\n\n"
            "# conf json:///tmp/csm.conf get_keys -key_index true\n\n"
            "# conf json:///tmp/csm.conf get_keys -key_index false\n\n")
        s_parser.set_defaults(func=ConfCli.get_keys)
        s_parser.add_argument('-key_index', dest='key_index', help=
            "key_index={True|False} (default: True)\n"
            "when True, returns keys including array index\n"
            "e.g. In case of 'xxx[0],xxx[1]', only 'xxx' is returned\n\n")

class GetsKvCmd:
    """ Get keys command structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('get_kv', help=
            "Retrieves the list of keys and values\n."
            "Example command:\n"
            "# conf json:///tmp/csm.conf get_kv\n\n"
            "# conf json:///tmp/csm.conf get_kv -key_index true\n\n"
            "# conf json:///tmp/csm.conf get_kv -key_index false\n\n")
        s_parser.set_defaults(func=ConfCli.get_kv)
        s_parser.add_argument('-key_index', dest='key_index', help=
            "key_index={True|False} (default: True)\n"
            "when True, returns keys including array index\n"
            "e.g. In case of 'xxx[0],xxx[1]', only 'xxx' is returned\n\n")

def main():
    # Setup Parser
    parser = argparse.ArgumentParser(description='Conf Store CLI',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('url', help='URL for the ConfStore backend')
    sub_parser = parser.add_subparsers(title='command',
        help='represents the action from: set, get, delete\n\n', dest='command')

    # Add Command Parsers
    members = inspect.getmembers(sys.modules[__name__])
    for name, cls in members:
        if name != "Cmd" and name.endswith("Cmd"):
            cls.add_args(sub_parser)

    # Parse and Process Arguments
    try:
        args = parser.parse_args()
        ConfCli.init(args.url)
        out = args.func(args)
        if out is not None and len(out) > 0:
            if type(out) == dict:
                for key, val in out.items():
                    print(key, "=", val) 
            else:
                print(out)
        return 0

    except Exception as e:
        sys.stderr.write("%s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        return errno.EINVAL

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
