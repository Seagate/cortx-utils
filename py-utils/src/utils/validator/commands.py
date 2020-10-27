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

import sys
import os
import errno

from cortx.utils.validator.error import VError


class VCommand:
    """Base class for all the commands."""

    def __init__(self, args):
        self._args = args

    @property
    def args(self):
        return self._args

    @staticmethod
    def add_args(parser):
        raise VError(errno.EINVAL, "invalid command")


class NetworkVCommand(VCommand):
    """Network related commands."""

    _name = "network"

    def __init__(self, args):
        super(NetworkVCommand, self).__init__(args)

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from v_network import NetworkV

        self._network = NetworkV()

    @staticmethod
    def add_args(parser):
        """Add Network Command args for parsing."""

        parser1 = parser.add_parser(
            NetworkVCommand._name, help='Network Validations')
        parser1.add_argument('args', nargs='*', default=[], help='type')
        parser1.set_defaults(command=NetworkVCommand)

    def process(self):
        """Validate network connectivity ip1 ip2 ip3..."""

        self._network.validate(self.args)


class ConsulVCommand(VCommand):
    """Consul related commands."""

    _name = "consul"

    def __init__(self, args):
        super(ConsulVCommand, self).__init__(args)

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from v_consul import ConsulV

        self._consul = ConsulV()

    @staticmethod
    def add_args(parser):
        """Add Consul Command args for parsing."""

        parser1 = parser.add_parser(
            ConsulVCommand._name, help='Consul Validations')
        parser1.add_argument('args', nargs='*', default=[], help='type')
        parser1.set_defaults(command=ConsulVCommand)

    def process(self):
        """Validate consul status."""

        self._consul.validate(self.args)
