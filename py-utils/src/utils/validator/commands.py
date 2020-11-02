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
        self._v_type = args.v_type
        self._args = args.args

    @property
    def args(self):
        return self._args

    @property
    def v_type(self):
        return self._v_type

    @staticmethod
    def add_args(parser, cmd_class, cmd_name):
        """Add Command args for parsing."""
        parser1 = parser.add_parser(
            cmd_class.name, help='%s Validations' % cmd_name)
        parser1.add_argument('v_type', help='validation type')
        parser1.add_argument('args', nargs='*', default=[], help='args')
        parser1.set_defaults(command=cmd_class)


class NetworkVCommand(VCommand):
    """Network related commands."""

    name = "network"

    def __init__(self, args):
        super(NetworkVCommand, self).__init__(args)

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from v_network import NetworkV

        self._network = NetworkV()

    def process(self):
        """Validate network connectivity ip1 ip2 ip3..."""

        self._network.validate(self.v_type, self.args)


class ConsulVCommand(VCommand):
    """Consul related commands."""

    name = "consul"

    def __init__(self, args):
        super(ConsulVCommand, self).__init__(args)

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from v_consul import ConsulV

        self._consul = ConsulV()

    def process(self):
        """Validate consul status."""

        self._consul.validate(self.v_type, self.args)


class ElasticsearchVCommand(VCommand):
    """Elasticsearch related commands."""

    name = "elasticsearch"

    def __init__(self, args):
        super(ElasticsearchVCommand, self).__init__(args)

        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from v_elasticsearch import ElasticsearchV

        self._elasticsearch = ElasticsearchV()

    def process(self):
        """Validate elasticsearch status."""

        self._elasticsearch.validate(self.v_type, self.args)
