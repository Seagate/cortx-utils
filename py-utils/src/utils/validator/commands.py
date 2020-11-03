#!/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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

from .pacemaker import PacemakerHealth
from typing import NamedTuple, Any


class CommandArgs(NamedTuple):
    args: Any
    v_type: str


class VCommand:
    """Base class for all the commands."""

    # TODO [KN] Make constructor not dependent on parsing results
    # This will allow to make add_args() non-static and thus will simplify the
    # use in subclasses.
    def __init__(self, args):
        self._v_type = args.v_type
        self._args = args.args

    @property
    def args(self):
        return self._args

    @property
    def v_type(self):
        return self._v_type

    @classmethod
    def add_args(cls, parser):
        """Add Command args for parsing."""
        cmd_class = cls
        cmd_name = cls.name

        parser1 = parser.add_parser(
            cmd_class.name, help='%s Validations' % cmd_name)
        parser1.add_argument('v_type', help='validation type')
        parser1.add_argument('args', nargs='*', default=[], help='args')
        parser1.set_defaults(command=cmd_class)


class NetworkVCommand(VCommand):
    """Network related commands."""

    name = "network"

    def __init__(self, args):
        super().__init__(args)

        from .v_network import NetworkV

        self._network = NetworkV()

    def process(self):
        """Validate network connectivity ip1 ip2 ip3..."""

        self._network.validate(self.v_type, self.args)


class ConsulVCommand(VCommand):
    """Consul related commands."""

    name = "consul"

    def __init__(self, args):
        super().__init__(args)

        from .v_consul import ConsulV

        self._consul = ConsulV()

    def process(self):
        """Validate consul status."""

        self._consul.validate(self.v_type, self.args)


class StorageVCommand(VCommand):
    """Storage related commands."""

    name = "storage"

    def __init__(self, args):
        super(StorageVCommand, self).__init__(args)

        from .v_storage import StorageV

        self._storage = StorageV()

    def process(self):
        """Validate storage status."""

        self._storage.validate(self.v_type, self.args)


class SaltVCommand(VCommand):
    """Salt related commands."""

    name = "salt"

    def __init__(self, args):
        super(SaltVCommand, self).__init__(args)

        from .v_salt import SaltV

        self._salt = SaltV()

    def process(self):
        """Validate salt minion connectivity <nodes>..."""

        self._salt.validate(self.v_type, self.args)


class BmcVCommand(VCommand):
    """BMC related commands."""

    name = "bmc"

    def __init__(self, args):
        super(BmcVCommand, self).__init__(args)

        from .v_bmc import BmcV

        self._bmc = BmcV()

    def process(self):
        """Validate bmc status."""

        self._bmc.validate(self.v_type, self.args)


class ElasticsearchVCommand(VCommand):
    """Elasticsearch related commands."""

    name = "elasticsearch"

    def __init__(self, args):
        super(ElasticsearchVCommand, self).__init__(args)

        from .v_elasticsearch import ElasticsearchV

        self._elasticsearch = ElasticsearchV()

    def process(self):
        """Validate elasticsearch status."""

        self._elasticsearch.validate(self.v_type, self.args)


class PacemakerCommand(VCommand):
    """Pacemaker-related checks."""
    name = 'pacemaker'

    def __init__(self, args):
        fake_args = CommandArgs(args=args, v_type='')
        super().__init__(fake_args)

    @classmethod
    def add_args(cls, parser):
        """Add Command args for parsing."""
        def validate_config(cmd: PacemakerCommand):
            cmd._validate_config()

        pcs_parser = parser.add_parser(cls.name, help='Pacemaker Validations')
        subp = pcs_parser.add_subparsers()

        conf_parser = subp.add_parser('configured',
                                      help='Basic sanity check of Pacemaker')

        conf_parser.add_argument('--stub',
                                 dest='handler_fn',
                                 default=validate_config,
                                 help=argparse.SUPPRESS)

        pcs_parser.set_defaults(command=cls)

    def process(self):
        handler = self._args.handler_fn
        handler(self)

    def _validate_config(self):
        pcs = PacemakerHealth()
        pcs.ensure_configured()
