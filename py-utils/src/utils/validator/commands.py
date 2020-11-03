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

from typing import Any, List

from .v_bmc import BmcV
from .v_consul import ConsulV
from .v_elasticsearch import ElasticsearchV
from .v_network import NetworkV
from .v_salt import SaltV
from .v_storage import StorageV


class VCommand:
    """Base class for all the commands."""
    def __init__(self, cli_args: List[str]):
        self._args = cli_args
        self._v_type = None
        self._validator = self.create_validator()

    def create_validator(self) -> Any:
        """Factory method that knows how to instantiate the proper validatorV.
        In the simplest case this is the only method to be overriden in a
        custom Command class.
        """
        raise NotImplementedError()

    @property
    def args(self):
        return self._args

    @property
    def v_type(self):
        return self._v_type

    def set_parsed_args(self, args):
        self._parsed_args = args
        self._v_type = args.v_type

    def process(self) -> None:
        """Process the given CLI command. Note that args is the parsed
        arguments provided by ArgParse"""

        self._validator.validate(self.v_type, self.args)

    def add_args(self, parser):
        """Add Command args for parsing."""
        cmd_name = self.name

        parser1 = parser.add_parser(cmd_name, help='%s Validations' % cmd_name)
        parser1.add_argument('v_type', help='validation type')
        parser1.add_argument('args', nargs='*', default=[], help='args')
        parser1.set_defaults(command=self)


class NetworkCommand(VCommand):
    """Network related commands."""

    name = "network"

    def create_validator(self) -> Any:
        return NetworkV()


class ConsulCommand(VCommand):
    """Consul related commands."""

    name = "consul"

    def create_validator(self) -> Any:
        return ConsulV()


class StorageCommand(VCommand):
    """Storage related commands."""

    name = "storage"

    def create_validator(self) -> Any:
        return StorageV()


class SaltCommand(VCommand):
    """Salt related commands."""

    name = "salt"

    def create_validator(self) -> Any:
        return SaltV()


class BmcCommand(VCommand):
    """BMC related commands."""

    name = "bmc"

    def create_validator(self) -> Any:
        return BmcV()


class ElasticsearchCommand(VCommand):
    """Elasticsearch related commands."""

    name = "elasticsearch"

    def create_validator(self) -> Any:
        return ElasticsearchV()
