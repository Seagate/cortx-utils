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

import traceback
import shutil
import sysconfig
from pathlib import Path

from cortx.utils.conf_store import Conf

class KafkaSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" %(self._rc, self._desc,
            traceback.format_exc())

    @property
    def rc(self):
        return self._rc


class Kafka:
    """ Represents Kafka and Performs setup related actions """

    def __init__(self, conf_url):
        self.index = "kafka"
        Conf.load(self.index, conf_url)

    def validate(self, phase: str):
        """ Perform validtions. Raises exceptions if validation fails """

        # Perform RPM validations
        return

    def post_install(self):
        """ Performs post install operations. Raises exception on error """

        # Copying systemd files from cortx package to /etc/systemd
        src_path = Path('/opt/seagate/cortx/utils/conf/')
        dest_path = Path('/etc/systemd/system/')
        for elem in src_path.iterdir():
            if '.service' in elem.parts[-1]:
                shutil.copy(elem, dest_path)
        # Perform actual operation. Obtain inputs using Conf.get(self.index, ..)
        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(self.index, ..)
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(self.index, ..)
        return 0

    def test(self, plan):
        """ Perform configuration testing. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(self.index, ..)
        return 0

    def reset(self):
        """ Performs Configuraiton reset. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(self.index, ..)
        return 0

