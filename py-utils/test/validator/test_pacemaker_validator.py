#!/usr/bin/env python3

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

# flake8: noqa: E401

import inspect
import os
import unittest
from typing import List
from unittest.mock import MagicMock

from cortx.utils.validator.error import VError
from cortx.utils.validator.v_pacemaker import (PacemakerClient, PacemakerV,
                                               Resource, StonithParser,
                                               StonithResource)


def mock_methods(obj, except_names: List[str] = []):
    """
    Makes sure that all public methods in the given object are replaced with
    a Mock that will raise an error when the method is invoked.

    Can be helpful to ensure that the object under test doesn't depend on a
    side effects that are not controlled by the unit test explicitly.
    """

    # [KN] By some reason there is no clean way to make all public methods
    # mocked just by default. But in test we are usually interested in the
    # certain methods only, if other ones are invoked,
    # this should mean FAILURE.

    assert obj is not None
    skip_set = set(except_names)
    members = inspect.getmembers(obj)
    func_names = [
        name for (name, val) in members if not name.startswith('_')
        and inspect.ismethod(val) and name not in skip_set
    ]

    for n in func_names:
        setattr(
            obj, n,
            MagicMock(
                side_effect=Exception(f'Unexpected invocation: function {n}')))
    return obj


def contents(filename: str) -> str:
    dirname = os.path.dirname(os.path.realpath(__file__))
    fullpath = f'{dirname}/{filename}'
    assert os.path.isfile(fullpath), f'No such file: {fullpath}'
    with open(fullpath) as f:
        s = f.read()
    return s


GOOD_XML = contents('pacemaker-2node.xml')


class StonithParserTest(unittest.TestCase):
    def test_parser_works(self):
        p = StonithParser()
        raw_text = '''
 Resource: stonith-c1 (class=stonith type=fence_ipmilan)
  Attributes: delay=5 ipaddr=10.230.244.112 login=ADMIN passwd=adminBMC! pcmk_host_check=static-list pcmk_host_list=srvnode-1 power_timeout=40
  Operations: monitor interval=10s (stonith-c1-monitor-interval-10s)
'''
        result = p.parse(raw_text)
        self.assertIsNotNone(result)
        self.assertEqual('stonith', result.klass)
        self.assertEqual('fence_ipmilan', result.typename)
        self.assertEqual('10.230.244.112', result.ipaddr)
        self.assertEqual('ADMIN', result.login)
        self.assertEqual('adminBMC!', result.passwd)

    def test_only_ipmi_supported(self):
        p = StonithParser()
        raw_text = '''
 Resource: stonith-c1 (class=stonith type=fence_dummy)
  Attributes: delay=5 ipaddr=10.230.244.112 login=ADMIN passwd=adminBMC! pcmk_host_check=static-list pcmk_host_list=srvnode-1 power_timeout=40
  Operations: monitor interval=10s (stonith-c1-monitor-interval-10s)
'''
        with self.assertRaises(AssertionError):
            p.parse(raw_text)

    def test_emptyilnes_ignored(self):
        p = StonithParser()
        raw_text = '''

 Resource: stonith-c1 (class=stonith type=fence_ipmilan)

  Attributes: delay=5 ipaddr=10.230.244.112 login=ADMIN passwd=adminBMC! pcmk_host_check=static-list pcmk_host_list=test-2 power_timeout=40
  Operations: monitor interval=10s (stonith-c1-monitor-interval-10s)
'''
        result = p.parse(raw_text)
        self.assertIsNotNone(result)
        self.assertEqual('stonith', result.klass)
        self.assertEqual('fence_ipmilan', result.typename)
        self.assertEqual('10.230.244.112', result.ipaddr)
        self.assertEqual('ADMIN', result.login)
        self.assertEqual('adminBMC!', result.passwd)
        self.assertEqual('test-2', result.pcmk_host_list)


class TestPacemakerClient(unittest.TestCase):
    def test_stonith_resources_found(self):
        client = PacemakerClient()
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])
        resources = client.get_stonith_resources()
        self.assertEqual(2, len(resources))
        self.assertEqual(['stonith-c1', 'stonith-c2'],
                         [t.id for t in resources])

    def test_fenced_nodes_extracted_from_stonith_resources(self):
        stonith_text = '''
 Resource: stonith-c1 (class=stonith type=fence_ipmilan)
  Attributes: delay=5 ipaddr=10.230.244.112 login=ADMIN passwd=adminBMC! pcmk_host_check=static-list pcmk_host_list=srvnode-1 power_timeout=40
  Operations: monitor interval=10s (stonith-c1-monitor-interval-10s)
'''
        client = PacemakerClient()
        client._get_full_status_xml = MagicMock(side_effect=[])
        client._get_stonith_resource_details_text = MagicMock(
            side_effect=[stonith_text])
        stonith_res = client.get_stonith_resource_details('stonith-c2')
        self.assertEqual('srvnode-1', stonith_res.pcmk_host_list)


class TestPacemakerV(unittest.TestCase):
    def test_validate_corosync_fails_if_no_pcs_found(self):
        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client, except_names=['get_corosync_status'])
        client._execute = MagicMock(side_effect=VError(1, 'Bang!'))

        with self.assertRaises(VError):
            validator.validate_configured()

    def test_validate_corosync_fails_if_one_node_only(self):
        corosync_status = """

Membership information
----------------------
    Nodeid      Votes Name
         1          1 srvnode-1 (local)
        """

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client)
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])
        client.get_corosync_status = MagicMock(side_effect=[corosync_status])

        with self.assertRaises(VError):
            validator.validate_configured()

    def test_validate_corosync_works(self):
        corosync_status = """

Membership information
----------------------
    Nodeid      Votes Name
         1          1 srvnode-1 (local)
         2          1 srvnode-2
        """

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client)
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])
        client.get_corosync_status = MagicMock(side_effect=[corosync_status])

        # No exception happens
        validator.validate_configured()

    def test_validate_all_stonith_running_works(self):
        def stonith(name: str) -> Resource:
            return self._stonith(name, True)

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client)
        client.get_stonith_resources = MagicMock(
            side_effect=[[stonith('c1'), stonith('c2')]])
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])

        validator.validate_all_stonith_running()

    def _stonith(self, name: str, active: bool) -> Resource:
        return Resource(id=name,
                        resource_agent='test',
                        role='role',
                        target_role='target_role',
                        active=active,
                        orphaned=False,
                        blocked=False,
                        managed=True,
                        failed=False,
                        failure_ignored=False,
                        nodes_running_on=1)

    def test_validate_all_stonith_running_fails_when_stonith_not_active(self):
        def stonith(name: str, running: int) -> Resource:
            return self._stonith(name, running == 1)

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client)
        client.get_stonith_resources = MagicMock(
            side_effect=[[stonith('c1', 1), stonith('c2', 0)]])
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])

        with self.assertRaises(VError):
            validator.validate_all_stonith_running()

    def test_validate_stonith_for_both_nodes_exist_works(self):
        def fake_details(name: str) -> StonithResource:
            name_map = {'stonith-c1': 'srvnode-2', 'stonith-c2': 'srvnode-1'}
            return StonithResource(klass='test',
                                   typename='typename',
                                   pcmk_host_list=name_map[name],
                                   ipaddr='ipaddr',
                                   login='login',
                                   passwd='passwd')

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client, except_names=['get_stonith_resources'])
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])
        client.get_stonith_resource_details = MagicMock(
            side_effect=fake_details)

        validator.validate_stonith_for_both_nodes_exist()

    def test_validate_stonith_for_both_nodes_exist_fails_if_node_missing(self):
        def fake_details(name: str) -> StonithResource:
            return StonithResource(klass='test',
                                   typename='typename',
                                   # the same node for every STONITH resource
                                   pcmk_host_list='srvnode-1',
                                   ipaddr='ipaddr',
                                   login='login',
                                   passwd='passwd')

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client, except_names=['get_stonith_resources'])
        client._get_full_status_xml = MagicMock(side_effect=[GOOD_XML])
        client.get_stonith_resource_details = MagicMock(
            side_effect=fake_details)

        with self.assertRaises(VError):
            validator.validate_stonith_for_both_nodes_exist()

    def test_validate_two_stonith_only_works(self):
        def stonith(name: str) -> Resource:
            return self._stonith(name, True)

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client)
        client.get_stonith_resources = MagicMock(
            side_effect=[[stonith('c1'), stonith('c2')]])

        validator.validate_two_stonith_only()

    def test_validate_two_stonith_only_fails_if_count_differs(self):
        def stonith(name: str) -> Resource:
            return self._stonith(name, True)

        client = PacemakerClient()
        validator = PacemakerV(executor=client)
        mock_methods(client)
        client.get_stonith_resources = MagicMock(
            side_effect=[[stonith(f'c{i}') for i in range(10)]])

        with self.assertRaises(VError):
            validator.validate_two_stonith_only()

