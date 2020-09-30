#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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

import json
import os

import networkx as nx

from cortx.utils.ha.hac import const


class Validator:
    def __init__(self):
        pass

    def execute(self):
        """Execute all function from _syntax_validations to validate schema."""
        method_list = \
            [v for v in dir(self) if callable(getattr(self, v)) and v.startswith("_validate")]
        for method in method_list:
            getattr(self, method)()


class SyntaxValidator(Validator):

    """
    SyntaxValidator check syntax for each input file
    NOTE: Add new function start with '_validate' to execute to check ha_spec
    """

    def __init__(self, filename):
        """Run all validation function for ha_spec."""
        super().__init__()
        self._schema_file = filename
        self._is_file()
        self._schema = self._is_valid_json()

    def get_schema(self):
        return self._schema

    def _is_file(self):
        """Verify file."""
        if not os.path.isfile(self._schema_file):
            raise Exception(f"{self._schema_file} is not a file.")

    def _is_valid_json(self):
        """Remove comment from file and validate for json."""
        try:
            with open(self._schema_file, "r") as spec_file:
                output_file = f"{self._schema_file}.parse"
                with open(output_file, "w") as parsed_file:
                    for a_line in spec_file.readlines():
                        line_no_spaces = a_line.strip()
                        if not line_no_spaces.startswith('#'):
                            parsed_file.writelines(a_line)
            with open(output_file, "r") as parsed_file:
                return json.load(parsed_file)
        except Exception as e:
            raise Exception(f"Invalid json file {self._schema_file}: {e}")

    def _validate_mode(self):
        """
        Validate mode for HA, It should be one of active_active, active_passive, primary_secondary
        Validate clone for mode of resources
        """

        for component in self._schema.keys():
            for resource in self._schema[component].keys():
                resource_mode = self._schema[component][resource]["ha"]["mode"]
                if resource_mode not in const.HA_MODES:
                    raise Exception(f"Invalid mode [{resource_mode}] for resource [{resource}] "
                                    f"in component {component}")

    def _validate_component_group(self):
        """validate component for each resource."""
        for component in self._schema.keys():
            for resource in self._schema[component].keys():
                resource_group = self._schema[component][resource]["group"]
                if resource_group not in const.HA_GROUP:
                    print(f"Warning: Invalid group [{resource_group}] for resource [{resource}] "
                          f"in component {component}")


class SymanticValidator(Validator):

    """SymanticValidator validate graph and compiled schema."""
    def __init__(self, compiled_schema, order_graph):
        super().__init__()
        self.compiled_schema = compiled_schema
        self.order_graph = order_graph

    def _validate_resource_predecessors(self):
        """Verify predecessors for resource."""
        error_msg = ""
        resource_set = self.compiled_schema["resources"]
        for resource in resource_set.keys():
            for predecessor in resource_set[resource]["dependencies"]["predecessors"]:
                if predecessor not in resource_set.keys():
                    error_msg += (f'Invalid predecessor resource [{predecessor}] in component '
                                  f'[{resource_set[resource]["component"]}]\n')
        if error_msg != "":
            raise Exception(error_msg)

    def _validate_resource_colocation(self):
        """Verify colocation for resource."""
        error_msg = ""
        resource_set = self.compiled_schema["resources"]
        for resource in resource_set.keys():
            for predecessors_resource in resource_set[resource]["dependencies"]["colocation"]:
                if predecessors_resource not in resource_set.keys():
                    error_msg += (f'Invalid colocation resource [{predecessors_resource}] in '
                                  f'component [{resource_set[resource]["component"]}]\n')
        if error_msg != "":
            raise Exception(error_msg)

    def _validate_resource_relation(self):
        """Verify relation for resource."""
        error_msg = ""
        resource_set = self.compiled_schema["resources"]
        for resource in resource_set.keys():
            for predecessors_resource in resource_set[resource]["dependencies"]["relation"]:
                if predecessors_resource not in resource_set.keys():
                    error_msg += (f'Invalid relation resource [{predecessors_resource}] '
                                  f'in component [{resource_set[resource]["component"]}]\n')
        if error_msg != "":
            raise Exception(error_msg)

    def _validate_cycle(self):
        """Verify graph to find cycle."""
        cycle_list = []
        cycle_gen = nx.simple_cycles(self.order_graph)
        for i in cycle_gen:
            cycle_list.append(i)
        if len(cycle_list) != 0:
            error_msg = ""
            for cycle in cycle_list:
                cycle.append(cycle[0])
                error_msg += f"Cycle found in graph {cycle}\n"
            raise Exception(error_msg)
