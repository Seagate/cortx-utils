#!/bin/env python3

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

import errno
import json
import time

from cortx.utils.process import SimpleProcess

class KafkaSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s" %(self._rc, self._desc)


class Utils:
    """ Represents Utils and Performs setup related actions """

    @staticmethod
    def validate(phase: str):
        """ Perform validtions """

        # Perform RPM validations
        return 0

    @staticmethod
    def post_install():
        """ Performs post install operations """
        return 0

    @staticmethod
    def init():
        """ Perform initialization """
        return 0

    @staticmethod
    def config(conf_url):
        """ Performs configurations """
        return 0

    @staticmethod
    def test():
        """ Perform configuration testing """
        return 0

    @staticmethod
    def reset():
        """ Performs Configuraiton reset """
        return 0
