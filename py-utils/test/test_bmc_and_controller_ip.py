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

    subcommand = "power status"
    valid_msg = "Chassis Power is on"
    bmc_data = dict()

    def setUp(self):
        self.cluster_id = self.fetch_salt_data('grains.get', const.CLUSTER_ID)
        self.node_list = self.fetch_salt_data('pillar.get', 'cluster')['node_list']
        for node in self.node_list:
            node_bmc = self.fetch_salt_data('pillar.get', 'cluster')[node]['bmc']
            self.bmc_data.update({node: node_bmc})

    @staticmethod
    def fetch_salt_data(func, arg):
        """Get value for any required key from salt"""
        result = salt.client.Caller().function(func, arg)
        if not result:
            raise VError(errno.EINVAL, "No result found for '%s'" % arg)
        return result

    def test_bmc_accessibility(self):
        """Check BMC IP is reachable"""
        for node in self.bmc_data.keys():
            username = self.bmc_data[node]['user']
            secret = self.bmc_data[node]['secret']
            key = Cipher.generate_key(self.cluster_id, 'cluster')
            password = Cipher.decrypt(key, secret.encode('ascii')).decode()
            ip = self.bmc_data[node]['ip']
            # check BMC ip is reachable
            self.assertRaises(VError, NetworkV().validate, [
                'connectivity', ip])
            # check BMC ip is accessible
            command = "sudo ipmitool -H " + ip + " -U " + username + \
                            " -P " + password + " -I " + "lan " + self.subcommand
            process = sp.Popen(command, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
            response = process.stdout.read().decode()
            assert self.valid_msg in response, \
                f"BMC IP {ip} is reachable but, not accessible."

    def tearDown(self):
        """Cleanup"""
        pass


class TestStorageEnclosureAccessibility(unittest.TestCase):
    """Test controller IPs are reachable and accessible"""

    name = "TestStorageEnclosureAccessibility"
    command = "show versions"
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
        ssh.connect(ip, port, username, password)
        self.connections.update({ip: ssh})

    def test_web_service(self):
        # TODO: validate web service availability
        pass

    def test_primary_mc(self):
        """Check primary MC is accessible"""
        # check primary ip is reachable
        self.assertRaises(VError, NetworkV().validate, [
            'connectivity', self.primary_mc])
        # check primary ip is accessible
        self._establish_connection(self.primary_mc)
        stdin, stdout, stderr = self.connections[self.primary_mc].exec_command(self.command)
        response = stdout.read().decode()
        assert self.valid_msg in response, \
            f"Storage enclosure primary IP {self.primary_mc} is reachable but, not accessible."

    def test_secondary_mc(self):
        """Check secondary MC is accessible"""
        # check secondary ip is reachable
        self.assertRaises(VError, NetworkV().validate, [
            'connectivity', self.secondary_mc])
        # check secondary ip is accessible
        self._establish_connection(self.secondary_mc)
        stdin, stdout, stderr = self.connections[self.secondary_mc].exec_command(self.command)
        response = stdout.read().decode()
        assert self.valid_msg in response, \
            f"Storage enclosure secondary IP {self.secondary_mc} is reachable but, not accessible."

    def tearDown(self):
        """Close ssh connection"""
        try:
            for conn in self.connections.keys():
                self.connections[conn].close()
        except Exception as err:
            print(f"{self.name}: WARN: {str(err)}")


if __name__ == '__main__':
    unittest.main()
