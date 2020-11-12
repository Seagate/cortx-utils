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

import unittest
import crypt
import errno
import sys
import os

from cortx.utils.comm import SSHSession
from cortx.utils.validator.error import VError

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)


class TestSSHSession(unittest.TestCase):
    """ Check ssh connection related validations """

    def setUp(self):
        """ Create temporary user for doing ssh on localhost """
        self.hostname = "localhost"
        self.__user = "utiltester"
        self.__passwd = "P@ssw0rd"
        e_pass = crypt.crypt(self.__passwd, "22")
        os.system(f"sudo useradd -m -p {e_pass} {self.__user}")

        # Let ssh connection be alive across all tests
        self.session = SSHSession(self.hostname, self.__user, self.__passwd)

    def test_connection_ok(self):
        """ Check if ssh connection is alive """
        if not self.session.is_connection_alive():
            raise VError(errno.EINVAL,
                f"Connection is lost with client '{self.session.host}'")

    def test_command_execution_ok(self):
        """ Check if command is executed successfully """
        cmd = "whoami"
        stdin, stdout, stderr = self.session.exec_command(cmd)
        cmd_output = stdout.read().decode()
        if self.__user not in cmd_output:
            raise VError(
                errno.EINVAL, f"Command execution failed on {self.hostname}.\
                                Command: '{cmd}'")

    def test_reconnect_ok(self):
        """ Check ssh re-connect after disconnection caller """
        # Close ssh connection
        self.session.disconnect()
        if self.session.is_connection_alive():
            raise VError(errno.EINVAL,
                f"SSH connection is not closed with client '{self.session.host}'")
        # Establish ssh to same client without invoking instance
        # and validate ssh connection is active
        self.session.connect()
        if not self.session.is_connection_alive():
            raise VError(errno.EINVAL,
                f"Connection is lost with client '{self.session.host}'")

    def tearDown(self):
        """ Cleanup the setup """
        self.session.disconnect()
        os.system(f"sudo userdel {self.__user}")


if __name__ == '__main__':
    unittest.main()
