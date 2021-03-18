#!/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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
from cortx.utils.validator.error import VError
from cortx.utils.conf_store import Conf

class ConfKeysV:
    """Confstore key validations."""

    def validate(self, v_type: str, index: str, keylist: list):
        """
        Process confstore key validations.
        Usage (arguments to be provided):
        1.  exists keylist <i.e. ['k1', 'k2>k3', ...]>
        """

        if v_type == "exists":
            return self.validate_keys(index, keylist)
        else:
            raise VError(errno.EINVAL,
                         "Action parameter %s not supported" % v_type)

    def validate_keys(self, index: str, keylist: list):
        """Check if each of keylist can be found in index of confstore."""
        for key in keylist:
            if Conf.get(index, key) is None:
                raise VError(errno.ENOENT, "key missing from the conf: '%s' " % key)
