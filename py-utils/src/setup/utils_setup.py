#!/bin/env python3

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
import sys
import errno
import inspect
import argparse
import traceback

from cortx.utils.common import CortxConf
from cortx.setup import Utils
from cortx.utils.log import Log
from cortx.setup.utils import SetupError


class Cmd:
    """ Setup Command """
    _index = 'setup'

    def __init__(self, args: dict):
        if os.geteuid() != 0:
            raise SetupError(errno.EPERM, "Permission denied! You need to be a \
                root user")
        self._url = args.config
        self._services = args.services
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
            f"usage: {prog} [-h] <cmd> --config <url> <args>...\n"
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
            if x.endswith('Cmd') and x != 'Cmd']
        for name, cmd in cmds:
            cmd.add_args(subparsers, cmd, name)
        args = parser.parse_args(argv)
        return args.command(args)

    @staticmethod
    def _add_extended_args(parser):
        """Override this method to add extended args."""
        return 0

    @staticmethod
    def add_args(parser: str, cls: str, name: str):
        """ Add Command args for parsing """

        parser1 = parser.add_parser(cls.name, help='setup %s' % name)
        parser1.add_argument('--config', help='Conf Store URL', type=str)
        parser1.add_argument('--services', help='Cortx Services', default='all')
        cls._add_extended_args(parser1)
        parser1.add_argument('args', nargs='*', default=[], help='args')
        parser1.set_defaults(command=cls)


class PostInstallCmd(Cmd):
    """ PostInstall Setup Cmd """
    name = 'post_install'

    def __init__(self, args: dict):
        super().__init__(args)

    def process(self):
        Utils.validate('post_install')
        rc = Utils.post_install(self._url)
        return rc


class PrepareCmd(Cmd):
    """ Prepare Setup Cmd """
    name = 'prepare'

    def __init__(self, args: dict):
        super().__init__(args)

    def process(self):
        return 0


class ConfigCmd(Cmd):
    """ Setup Config Cmd """
    name = 'config'

    def __init__(self, args):
        super().__init__(args)

    def process(self):
        Utils.validate('config')
        rc = Utils.config(self._url)
        return rc


class InitCmd(Cmd):
    """ Init Setup Cmd """
    name = 'init'

    def __init__(self, args):
        super().__init__(args)

    def process(self):
        Utils.validate('init')
        rc = Utils.init()
        return rc


class TestCmd(Cmd):
    """ Test Setup Cmd """
    name = 'test'

    @staticmethod
    def _add_extended_args(parser):
        parser.add_argument('--plan', default='sanity', help='Test Plan', \
            type=str)

    def __init__(self, args):
        super().__init__(args)
        # Default test_plan is 'sanity'
        self.test_plan = args.plan

    def process(self):
        Utils.validate('test')
        rc = Utils.test(self.test_plan)
        return rc


class ResetCmd(Cmd):
    """ Reset Setup Cmd """
    name = 'reset'

    def __init__(self, args):
        super().__init__(args)

    def process(self):
        Utils.validate('reset')
        rc = Utils.reset()
        return rc


class CleanupCmd(Cmd):
    """ Cleanup Setup Cmd """
    name = 'cleanup'

    @staticmethod
    def _add_extended_args(parser):
        parser.add_argument('--pre-factory', help=' Pre-Factory cleanup',\
            action='store_true')

    def __init__(self, args: dict):
        super().__init__(args)
        # hifen(-) in argparse is converted to underscore(_)
        # to make sure string is valid attrtibute
        self.pre_factory = args.pre_factory

    def process(self):
        Utils.validate('cleanup')
        rc = Utils.cleanup(self.pre_factory)
        return rc


class PreUpgradeCmd(Cmd):
    """ Manages post upgrade config changes """
    name = 'pre_upgrade'

    def __init__(self, args: dict):
        super().__init__(args)

    def process(self):
        Utils.validate('post_upgrade')
        rc = Utils.pre_upgrade(self.args[0])
        return rc


class PostUpgradeCmd(Cmd):
    """ Manages post upgrade config changes """
    name = 'post_upgrade'

    def __init__(self, args: dict):
        super().__init__(args)

    def process(self):
        Utils.validate('post_upgrade')
        rc = Utils.post_upgrade(self.args[0])
        return rc


def main():
    from cortx.utils.conf_store import Conf
    tmpl_file_index = 'tmpl_index'
    argv = sys.argv

    # Get the log path
    tmpl_file = argv[3]
    Conf.load(tmpl_file_index, tmpl_file, skip_reload=True)
    log_dir = Conf.get(tmpl_file_index, 'cortx>common>storage>log', \
        '/var/log')
    # utils_log_path = os.path.join(log_dir, 'cortx/utils')
    utils_log_path = CortxConf.get_log_path(base_dir=log_dir)

    # Get the log level
    log_level = CortxConf.get_key('utils>log_level', 'INFO')

    Log.init('utils_setup', utils_log_path, level=log_level, backup_count=5, \
        file_size_in_mb=5)
    try:
        desc = "CORTX Utils Setup command"
        Log.info(f"Starting utils_setup {argv[1]} ")
        command = Cmd.get_command(desc, argv[1:])
        rc = command.process()
    except SetupError as e:
        sys.stderr.write("error: %s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        Cmd.usage(argv[0])
        rc = e.rc
    except Exception as e:
        sys.stderr.write("error: %s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        rc = errno.EINVAL
    Log.info(f"Command {command} {argv[1]} finished with exit " \
        f"code {rc}")


if __name__ == '__main__':
    sys.exit(main())
