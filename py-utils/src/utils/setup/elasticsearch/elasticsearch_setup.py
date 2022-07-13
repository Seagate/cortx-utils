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

import sys
import errno
import inspect
import traceback
import argparse

from cortx.utils.setup.elasticsearch import Elasticsearch
from cortx.utils.setup.elasticsearch import ElasticsearchSetupError


class Cmd:
    """Setup Command."""

    _index = "setup"

    def __init__(self, args: dict):
        self._url = args.config
        self._args = args.args

    @property
    def args(self) -> str:
        return self._args

    @property
    def url(self) -> str:
        return self._url

    @staticmethod
    def usage(prog: str):
        """Print usage instructions."""
        sys.stderr.write(
            f"usage: {prog} [-h] <cmd> --config <url> <args>...\n"
            f"where:\n"
            f"cmd   post_install, prepare, config, init, reset, test, cleanup, pre_upgrade, post_upgrade\n"
            f"url   Config URL\n")

    @staticmethod
    def get_command(desc: str, argv: dict):
        """Return the Command after parsing the command line."""
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
    def _add_extended_args(parser):
        """Override this method to add extended args."""
        pass

    @staticmethod
    def add_args(parser: str, cls: str, name: str):
        """Add Command args for parsing."""
        parser1 = parser.add_parser(cls.name, help=f'setup {name}')
        parser1.add_argument('--config', help='Conf Store URL', type=str)
        cls._add_extended_args(parser1)
        parser1.add_argument('args', nargs='*', default=[], help='args')
        parser1.set_defaults(command=cls)


class PostInstallCmd(Cmd):
    """PostInstall Setup Cmd."""

    name = "post_install"

    def __init__(self, args: dict):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        self.elasticsearch.validate(self.name)
        rc = self.elasticsearch.post_install()
        return rc


class PrepareCmd(Cmd):
    """Prepare Setup Cmd."""

    name = "prepare"

    def __init__(self, args: dict):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        rc = self.elasticsearch.prepare()
        return rc


class ConfigCmd(Cmd):
    """Setup Config Cmd."""

    name = "config"

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        self.elasticsearch.validate(self.name)
        rc = self.elasticsearch.config()
        return rc


class InitCmd(Cmd):
    """Init Setup Cmd."""

    name = "init"

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        rc = self.elasticsearch.init()
        return rc


class TestCmd(Cmd):
    """Test Setup Cmd."""

    name = "test"

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        rc = self.elasticsearch.test()
        return rc


class ResetCmd(Cmd):
    """Reset Setup Cmd."""

    name = "reset"

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        rc = self.elasticsearch.reset()
        return rc


class CleanupCmd(Cmd):
    """Reset Setup Cmd."""

    name = "cleanup"

    @staticmethod
    def _add_extended_args(parser):
        parser.add_argument('--pre-factory', action="store_true",
                             help='Factory cleanup.')

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)
        self.pre_factory = args.pre_factory

    def process(self):
        rc = self.elasticsearch.cleanup(self.pre_factory)
        return rc


class PreUpgradeCmd(Cmd):
    """Pre Upgrade Setup Cmd."""

    name = "pre_upgrade"

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        rc = self.elasticsearch.pre_upgrade()
        return rc

class PostUpgradeCmd(Cmd):
    """Post Upgrade Setup Cmd."""

    name = "post_upgrade"

    def __init__(self, args):
        super().__init__(args)
        self.elasticsearch = Elasticsearch(args.config)

    def process(self):
        rc = self.elasticsearch.post_upgrade()
        return rc


def main(argv: dict):
    try:
        desc = "CORTX Elasticsearch Setup command"
        command = Cmd.get_command(desc, argv[1:])
        rc = command.process()
        if rc != 0:
            raise ValueError(f"Failed to run {argv[1]}")

    except ElasticsearchSetupError as err:
        sys.stderr.write(f"{str(err)}\n")
        Cmd.usage(argv[0])
        return err.rc()

    except Exception as err:
        sys.stderr.write(f"Error: {(str(err))}\n\n")
        sys.stderr.write(f"{traceback.format_exc()}\n")
        Cmd.usage(argv[0])
        return errno.EINVAL


if __name__ == '__main__':
    sys.exit(main(sys.argv))
