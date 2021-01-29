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

import errno


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

        from v_consul import ConsulV

        self._consul = ConsulV()

    def process(self):
        """Validate consul status."""

        self._consul.validate(self.v_type, self.args)


class StorageVCommand(VCommand):
    """Storage related commands."""

    name = "storage"

    def __init__(self, args):
        super(StorageVCommand, self).__init__(args)

        from v_storage import StorageV

        self._storage = StorageV()

    def process(self):
        """Validate storage status."""

        self._storage.validate(self.v_type, self.args)


class SaltVCommand(VCommand):
    """Salt related commands."""

    name = "salt"

    def __init__(self, args):
        super(SaltVCommand, self).__init__(args)

        from v_salt import SaltV

        self._salt = SaltV()

    def process(self):
        """Validate salt minion connectivity <nodes>..."""

        self._salt.validate(self.v_type, self.args)


class BmcVCommand(VCommand):
    """BMC related commands."""

    name = "bmc"

    def __init__(self, args):
        super(BmcVCommand, self).__init__(args)

        from v_bmc import BmcV

        self._bmc = BmcV()

    def process(self):
        """Validate bmc status."""

        self._bmc.validate(self.v_type, self.args)


class ElasticsearchVCommand(VCommand):
    """Elasticsearch related commands."""

    name = "elasticsearch"

    def __init__(self, args):
        super(ElasticsearchVCommand, self).__init__(args)

        from v_elasticsearch import ElasticsearchV

        self._elasticsearch = ElasticsearchV()

    def process(self):
        """Validate elasticsearch status."""

        self._elasticsearch.validate(self.v_type, self.args)


class ControllerVCommand(VCommand):
    """Controller related commands."""

    name = "controller"

    def __init__(self, args):
        super(ControllerVCommand, self).__init__(args)

        from v_controller import ControllerV

        self._controller = ControllerV()

    def process(self):
        """Validate controller status."""

        self._controller.validate(self.v_type, self.args)

class PkgVCommand(VCommand):
    """Pkg check related commands."""

    name = "Pkg"

    def __init__(self, args):
        super(PkgVCommand, self).__init__(args)

        from v_pkg import PkgV

        self._pkg = PkgV()

    def process(self):
        """Validate pkg status."""

        self._pkg.validate(self.v_type, self.args)

class ServiceVCommand(VCommand):
    """Service check related commands."""

    name = "Service"

    def __init__(self, args):
        super(ServiceVCommand, self).__init__(args)

        from v_service import ServiceV

        self._service = ServiceV()

    def process(self):
        """Validate service status."""

        self._service.validate(self.v_type, self.args)
