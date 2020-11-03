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
import subprocess as sp
import salt.client
import errno
import paramiko
from cortx.utils import const
from cortx.validator.error import VError
from cortx.utils.security.cipher import Cipher
from cortx.utils.validator.v_network import NetworkV


class TestBMCConnectivity(unittest.TestCase):
    """Test BMC IP is reachable and accessible"""

    def setUp(self):
        """Get bmc data"""
        command = "sudo salt-call grains.get id --output=newline_values_only"
        node = self.execute_command(command)
        self.node_bmc = self.fetch_salt_data('pillar.get', 'cluster')[node]['bmc']
        self.cluster_id = self.fetch_salt_data('grains.get', const.CLUSTER_ID)

    @staticmethod
    def fetch_salt_data(func, arg):
        """Get value for any required key from salt"""
        result = salt.client.Caller().function(func, arg)
        if not result:
            raise VError(errno.EINVAL, "No result found for '%s'" % arg)
        return result

    @staticmethod
    def execute_command(command):
        response = None
        process = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        response, error = process.communicate()
        if error:
            raise Exception(error)
        response = response.decode().strip()
        return response

    def test_bmc_accessibility(self):
        """Check BMC IP is reachable"""
        ip = self.node_bmc['ip']
        # check BMC ip is reachable
        self.assertRaises(VError, NetworkV().validate, [
            'connectivity', ip])
        # check BMC ip is accessible (in band)
        command = "sudo ipmitool channel info"
        response = self.execute_command(command)
        assert response, \
            f"BMC is reachable through inband KCS channel."

    def test_bmc_accessibility_over_lan(self):
        """Check BMC IP is accessible over lan"""
        ip = self.node_bmc['ip']
        username = self.node_bmc['user']
        secret = self.node_bmc['secret']
        key = Cipher.generate_key(self.cluster_id, 'cluster')
        password = Cipher.decrypt(key, secret.encode('ascii')).decode()
        # check BMC ip is accessible over lan (out of band)
        command = "sudo ipmitool -H " + ip + " -U " + username + \
                        " -P " + password + " -I " + "lan channel info"
        response = self.execute_command(command)
        assert response, \
            f"BMC is reachable over the lan."

    def tearDown(self):
        """Cleanup"""
        pass


class TestStorageEnclosureAccessibility(unittest.TestCase):
    """Test controller IPs are reachable and accessible"""

    name = "TestStorageEnclosureAccessibility"
    command = "show versions"
    mc_supported = ['GN265', 'GN280']
    valid_msg = "Command completed successfully"

    def setUp(self):
        """Get primary and secondary MC of storage controller"""
        self.connections = dict()
        self.cluster_id = self.fetch_salt_data('grains.get', const.CLUSTER_ID)
        self.enclosure_data = self.fetch_salt_data('pillar.get', const.STORAGE_ENCLOSURE)
        self.primary_mc = self.enclosure_data['controller']['primary_mc']['ip']
        self.secondary_mc = self.enclosure_data['controller']['secondary_mc']['ip']

    @staticmethod
    def fetch_salt_data(func, arg):
        """Get value for any required key from salt"""
        result = salt.client.Caller().function(func, arg)
        if not result:
            raise VError(errno.EINVAL, "No result found for '%s'" % arg)
        return result

    def _establish_connection(self, ip, port="22"):
        """Create ssh connection to storage enclosure"""
        username = self.enclosure_data['controller']['user']
        secret = self.enclosure_data['controller']['secret']
        key = Cipher.generate_key(self.cluster_id, const.STORAGE_ENCLOSURE)
        password = Cipher.decrypt(key, secret.encode('ascii')).decode()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(ip, port, username, password)
            self.connections.update({ip: ssh})
        except:
            return False
        return True

    def test_web_service(self):
        # TODO: validate web service availability
        pass

    def test_primary_mc(self):
        """Check primary MC is accessible"""
        # check primary ip is reachable
        self.assertRaises(VError, NetworkV().validate, [
            'connectivity', self.primary_mc])
        # check primary ip is accessible
        assert not self._establish_connection(self.primary_mc), \
                    "Storage enclosure primary IP {self.primary_mc} is not accessible."
        # check command execution on primary MC
        stdin, stdout, stderr = self.connections[self.primary_mc].exec_command(self.command)
        response = stdout.read().decode()
        assert self.valid_msg in response, \
            f"Failed to execute command on primary MC {self.primary_mc}"
        # check supported bundle version of MC
        is_supported = any(ver for ver in self.mc_supported if ver in response)
        assert is_supported, \
            f"Unsupported controller bundle version found on enclosure."

    def test_secondary_mc(self):
        """Check secondary MC is accessible"""
         # check secondary ip is reachable
        self.assertRaises(VError, NetworkV().validate, [
            'connectivity', self.secondary_mc])
        # check secondary ip is accessible
        assert not self._establish_connection(self.secondary_mc), \
                    "Storage enclosure secondary IP {self.secondary_mc} is not accessible."
        # check command execution on secondary MC
        stdin, stdout, stderr = self.connections[self.secondary_mc].exec_command(self.command)
        response = stdout.read().decode()
        assert self.valid_msg in response, \
            f"Failed to execute command on primary MC {self.secondary_mc}"
        # check supported bundle version of MC
        is_supported = any(ver for ver in self.mc_supported if ver in response)
        assert is_supported, \
            f"Unsupported controller bundle version found on enclosure."


    def tearDown(self):
        """Close ssh connection"""
        try:
            for conn in self.connections.keys():
                self.connections[conn].close()
        except Exception as err:
            print(f"{self.name}: WARN: {str(err)}")


if __name__ == '__main__':
    unittest.main()
