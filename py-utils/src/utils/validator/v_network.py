#!/bin/env python3

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

import os
import errno

from cortx.utils.validator.error import VError

class NetworkV:
    """ Network related validations """
    def __init__(self):
        # TODO: Perform initialization for network level commands
        pass

    def validate(self, args):
        """ Process network valiations """

        if not isinstance(args, list) or len(args) < 2:
            raise VError(errno.EINVAL, "Invalid parameters %s" %args)

        action = args[0]

        # TODO Write actual code here
        if action == "iface": 
            self.validate_iface(args[1])

    def validate_iface(self, iface):
        # TODO: This is sample. Need to add actual network validation
        
        iface_list = os.listdir("/sys/class/net/")
        if iface in iface_list:
            return

        raise Exception(errno.ENOENT, "No such interface %s" %iface)
