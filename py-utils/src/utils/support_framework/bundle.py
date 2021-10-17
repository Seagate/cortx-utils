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


class Bundle:
    def __init__(self, bundle_id, bundle_path, comment, node_name, components):
        """Initialiases bundle object, which will have support bundle information."""
        self._bundle_id = bundle_id
        self._bundle_path = bundle_path
        self._comment = comment
        self._node_name = node_name
        self._components = components

    @property
    def bundle_id(self):
        return self._bundle_id

    @property
    def bundle_path(self):
        return self._bundle_path

    @property
    def node_name(self):
        return self._node_name

    @property
    def comment(self):
        return self._comment

    @property
    def components(self):
        return self._components
