# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import unittest
from unittest.mock import MagicMock

from cortx.utils.validator.v_ha import HaStatusV, ServiceInfo
from cortx.utils.validator.error import VError


def service(name, status):
    return ServiceInfo(name=name, status=status)


def empty():
    return


class TestHaValidator(unittest.TestCase):
    """Test HA Status-related validations."""
    def test_services_found(self):
        validator = HaStatusV()
        status = '''
Data pool:
    # fid name
    0x6f00000000000001:0x2e 'the pool'
Profile:
    # fid name: pool(s)
    0x7000000000000001:0x4e 'default': 'the pool' None None
Services:
    localhost  (RC)
    [started]  hax        0x7200000000000001:0x6   192.168.6.214@tcp:12345:1:1
    [started]  confd      0x7200000000000001:0x9   192.168.6.214@tcp:12345:2:1
    [started]  ioservice  0x7200000000000001:0xc   192.168.6.214@tcp:12345:2:2
    [unknown]  m0_client  0x7200000000000001:0x28  192.168.6.214@tcp:12345:4:1
    [unknown]  m0_client  0x7200000000000001:0x2b  192.168.6.214@tcp:12345:4:2
        '''

        result = validator._extract_service_info(status)
        self.assertEqual(len(result), 5)
        s = service
        self.assertEqual(result, [
            s('hax', 'started'),
            s('confd', 'started'),
            s('ioservice', 'started'),
            s('m0_client', 'unknown'),
            s('m0_client', 'unknown')
        ])

    def test_validator_works_when_all_started(self):
        validator = HaStatusV()
        status = '''
Data pool:
    # fid name
    0x6f00000000000001:0x2e 'the pool'
Profile:
    # fid name: pool(s)
    0x7000000000000001:0x4e 'default': 'the pool' None None
Services:
    localhost  (RC)
    [started]  hax        0x7200000000000001:0x6   192.168.6.214@tcp:12345:1:1
    [started]  confd      0x7200000000000001:0x9   192.168.6.214@tcp:12345:2:1
    [started]  ioservice  0x7200000000000001:0xc   192.168.6.214@tcp:12345:2:2
    [started]  m0_client  0x7200000000000001:0x28  192.168.6.214@tcp:12345:4:1
    [started]  m0_client  0x7200000000000001:0x2b  192.168.6.214@tcp:12345:4:2
        '''

        validator._ensure_hctl_available = MagicMock(side_effect=empty)
        validator._get_hctl_status = MagicMock(side_effect=[status])

        # No exception is thrown
        validator.validate_io_stack_sane()

    def test_validator_works_when_all_io_started(self):
        validator = HaStatusV()
        status = '''
Data pool:
    # fid name
    0x6f00000000000001:0x2e 'the pool'
Profile:
    # fid name: pool(s)
    0x7000000000000001:0x4e 'default': 'the pool' None None
Services:
    localhost  (RC)
    [unknown]  hax        0x7200000000000001:0x6   192.168.6.214@tcp:12345:1:1
    [unknown]  confd      0x7200000000000001:0x9   192.168.6.214@tcp:12345:2:1
    [started]  ioservice  0x7200000000000001:0xc   192.168.6.214@tcp:12345:2:2
    [started]  m0_client  0x7200000000000001:0x28  192.168.6.214@tcp:12345:4:1
    [started]  m0_client  0x7200000000000001:0x2b  192.168.6.214@tcp:12345:4:2
        '''

        validator._ensure_hctl_available = MagicMock(side_effect=empty)
        validator._get_hctl_status = MagicMock(side_effect=[status])

        # No exception is thrown
        validator.validate_io_stack_sane()

    def test_validator_fails_when_io_unknown(self):
        validator = HaStatusV()
        status = '''
Data pool:
    # fid name
    0x6f00000000000001:0x2e 'the pool'
Profile:
    # fid name: pool(s)
    0x7000000000000001:0x4e 'default': 'the pool' None None
Services:
    localhost  (RC)
    [unknown]  hax        0x7200000000000001:0x6   192.168.6.214@tcp:12345:1:1
    [unknown]  confd      0x7200000000000001:0x9   192.168.6.214@tcp:12345:2:1
    [started]  ioservice  0x7200000000000001:0xc   192.168.6.214@tcp:12345:2:2
    [started]  m0_client  0x7200000000000001:0x28  192.168.6.214@tcp:12345:4:1
    [unknown]  m0_client  0x7200000000000001:0x2b  192.168.6.214@tcp:12345:4:2
        '''

        validator._ensure_hctl_available = MagicMock(side_effect=empty)
        validator._get_hctl_status = MagicMock(side_effect=[status])

        with self.assertRaises(VError):
            validator.validate_io_stack_sane()

    def test_validator_fails_when_no_services_found(self):
        validator = HaStatusV()
        status = '''
Data pool:
    # fid name
    0x6f00000000000001:0x2e 'the pool'
Profile:
    # fid name: pool(s)
    0x7000000000000001:0x4e 'default': 'the pool' None None
Services:
    localhost  (RC)
        '''

        validator._ensure_hctl_available = MagicMock(side_effect=empty)
        validator._get_hctl_status = MagicMock(side_effect=[status])

        with self.assertRaises(VError):
            validator.validate_io_stack_sane()

    def test_validator_fails_when_status_not_understood(self):
        validator = HaStatusV()
        status = '''
Data pool:
    # fid name
    0x6f00000000000001:0x2e 'the pool'
Profile:
    # fid name: pool(s)
    0x7000000000000001:0x4e 'default': 'the pool' None None
Services:
    localhost  (RC)
    BROKENunknown]  hax        0x7200000000000001:0x6   192.168.6.214@tcp:12345:1:1
    BROKENunknown]  confd      0x7200000000000001:0x9   192.168.6.214@tcp:12345:2:1
    BROKENstarted]  ioservice  0x7200000000000001:0xc   192.168.6.214@tcp:12345:2:2
    BROKENstarted]  m0_client  0x7200000000000001:0x28  192.168.6.214@tcp:12345:4:1
    BROKENunknown]  m0_client  0x7200000000000001:0x2b  192.168.6.214@tcp:12345:4:2
        '''

        validator._ensure_hctl_available = MagicMock(side_effect=empty)
        validator._get_hctl_status = MagicMock(side_effect=[status])

        with self.assertRaises(VError):
            validator.validate_io_stack_sane()
