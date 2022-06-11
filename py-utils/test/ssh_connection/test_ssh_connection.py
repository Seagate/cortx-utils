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

from cortx.utils.ssh import SSHChannel
from cortx.utils.validator.error import VError

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)


class TestSSHChannel(unittest.TestCase):
    """Check ssh connection related validations."""

    @classmethod
    def setUpClass(cls):
        """Create temporary user for doing ssh on localhost."""
        cls.hostname = "localhost"
        cls.__user = "utiltester"
        cls.__passwd = "P@ssw0rd"
        e_pass = crypt.crypt(cls.__passwd, "22")
        os.system(f"sudo useradd -M -p {e_pass} {cls.__user}")

        # Let ssh connection be alive across all tests
        cls.session = SSHChannel(cls.hostname, cls.__user, cls.__passwd, sftp_enabled=True)

    def test_connection_ok(self):
        """Check if ssh connection is alive."""
        if not self.session.is_connection_alive():
            raise VError(errno.EINVAL,
                f"Connection is lost with client '{self.session.host}'")

    def test_command_execution_ok(self):
        """Check if command is executed successfully."""
        cmd = "whoami"
        rc, output = self.session.execute(cmd)
        if rc !=0  or self.__user not in output:
            raise VError(
                errno.EINVAL, f"Command execution failed on {self.hostname}.\
                                Command: '{cmd}'\
                                Return Code: {rc}")

    def test_reconnect_ok(self):
        """Check ssh re-connect after disconnection caller."""
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

    def test_send_file(self):
        # Create local file
        local_file = '/tmp/test_file.txt'
        fObj = open(local_file, 'w')
        fObj.close()
        # Send file to remote location
        remote_dir = '/tmp/tmp_remote/'
        os.makedirs(remote_dir, exist_ok=True)
        os.chmod(remote_dir, 0o657)
        remote_file = os.path.join(remote_dir, 'test_file.txt')
        self.session.send_file(local_file, remote_file)
        os.remove(local_file)
        os.system(f"rm -rf {remote_dir}")

    def test_recv_file(self):
        # Create remote file
        remote_dir = '/tmp/tmp_remote/'
        os.makedirs(remote_dir, exist_ok=True)
        remote_file = os.path.join(remote_dir, 'test_file.txt')
        fObj = open(remote_file, 'w')
        fObj.close()
        # Receive file from remote location
        local_file = '/tmp/test_file.txt'
        self.session.recv_file(remote_file, local_file)
        os.remove(remote_file)

    @classmethod
    def tearDownClass(cls):
        """Cleanup the setup."""
        cls.session.disconnect()
        os.system(f"sudo userdel {cls.__user}")


if __name__ == '__main__':
    unittest.main()
