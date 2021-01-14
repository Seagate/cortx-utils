#!/bin/env python3

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

import sys
import errno
import argparse
import inspect
import traceback

from cortx.utils.conf_store import Conf
from cortx.utils.setup import Utils


class Cmd:
    """ Setup Command """
    _index = "setup"

    def __init__(self, args: dict):
        self._url = args.url
        Conf.load(self._index, self._url)
        self._args = args.args

    @property
    def args(self) -> str:
        return self._args

    @property
    def url(self) -> str:
        return self._url

    @staticmethod
    def usage(prog: str):
        """ Print usage instructions """

        sys.stderr.write(
            f"usage: {prog} [-h] <cmd> <url> <args>...\n"
            f"where:\n"
            f"cmd   post_install, config, init, reset, test\n"
            f"url   Config URL\n")

    @staticmethod
    def get_command(desc: str, argv: dict):
        """ Return the Command after parsing the command line. """

        parser = argparse.ArgumentParser(desc)

        subparsers = parser.add_subparsers()
        cmds = inspect.getmembers(sys.modules[__name__])
        cmds = [(x, y) for x, y in cmds
            if x.endswith("Cmd") and x != "Cmd"]
        for name, cmd in cmds:
            cmd.add_args(subparsers, cmd, name)
        args = parser.parse_args(argv)
        return args.command(args)

    @staticmethod
    def add_args(parser: str, cls: str, name: str):
        """ Add Command args for parsing."""

        parser1 = parser.add_parser(cls.name, help='setup %s' % name)
        parser1.add_argument('url', help='Conf Store URL')
        parser1.add_argument('args', nargs='*', default=[], help='args')
        parser1.set_defaults(command=cls)


class PostInstallCmd(Cmd):
    """ PostInstall Setup Cmd """
    name = "postinstall"

    def __init__(self, args: dict):
        super().__init__(args)

    def process(self):
        Utils.validate('post_install')
        Utils.post_install()


class ConfigCmd(Cmd):
    """ Setup Config Cmd """
    name = "config"

    def __init__(self, args):
        super().__init__(args)

    def process(self):
        Utils.validate('config')
        Utils.config()


class InitCmd(Cmd):
    """ Init Setup Cmd """
    name = "init"

    def __init__(self, args):
        super().__init__(args)

    def process(self):
        Utils.validate('init')
        Utils.init()


def main(argv: dict):
    try:
        desc = "CORTX Utils Setup command"
        command = Cmd.get_command(desc, argv[1:])
        command.process()

    except Exception as e:
        sys.stderr.write("error: %s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        Cmd.usage(argv[0])
        return errno.EINVAL


if __name__ == '__main__':
    sys.exit(main(sys.argv))
