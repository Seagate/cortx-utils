#!/bin/python3

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

class VError(Exception):
    """Class representing a generic error with error code and output of a command."""

    def __init__(self, rc, desc):
        self._rc = rc
        self._desc = desc

        error = "%s: %s" % (self._rc, self._desc)
        super(VError, self).__init__(error)

    @property
    def rc(self):
        return self._rc

    @property
    def desc(self):
        return self._desc
