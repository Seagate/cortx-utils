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

import logging
import re
from errno import EINVAL, ERANGE
from subprocess import PIPE, Popen  # nosec
from typing import Any, Dict, List, Match, NamedTuple, Optional, Tuple

import defusedxml.ElementTree as ET

from .error import VError

Resource = NamedTuple('Resource', [('id', str), ('resource_agent', str),
                                   ('role', str), ('target_role', str),
                                   ('active', bool), ('orphaned', bool),
                                   ('blocked', bool), ('managed', bool),
                                   ('failed', bool), ('failure_ignored', bool),
                                   ('nodes_running_on', int)])

StonithResource = NamedTuple('StonithResource',
                             [('klass', str), ('typename', str),
                              ('pcmk_host_list', str), ('ipaddr', str),
                              ('login', str), ('passwd', str)])


def _to_bool(value: str) -> bool:
    return 'true' == value


class StonithParser:
    """
    Parser for 'pcs stonith show <id>' command output.
    Analyzes the ouput of CLI command and converts to List[StonithResource]
    """

    def _parse_kv(self, text: str) -> Dict[str, str]:
        def _pair(lst: List[str]) -> Tuple[str, str]:
            return (lst[0], lst[1])

        return dict(_pair(kv.split('=')) for kv in text.split(' '))

    def parse(self, raw_text: str) -> StonithResource:
        lines = raw_text.splitlines()

        def apply_re(regex: str, text_to_match: str) -> Match:
            match = re.match(regex, text_to_match)
            if not match:
                raise RuntimeError(
                    'Output of "pcs stonith show <name>" was not understood')
            return match

        def get_line() -> str:
            while True:
                if not lines:
                    raise StopIteration()
                result = lines.pop(0).strip()
                if result:
                    return result

        # First non-empty line: Resource: <ID> (class=<ID> type=fence_ipmilan)
        s = get_line()
        match = apply_re(
            r'^\s*Resource: ([^ ]+) \(class=([^ ]+) type=([^\)]+).*$', s)
        klass = match.group(2)
        typename = match.group(3)
        assert typename == 'fence_ipmilan'

        # Second non-empty line: Attributes: [key=value]( [key=value])*
        match = apply_re(r'^\s*Attributes: (.*)$', get_line())
        attr_dict = self._parse_kv(match.group(1))
        return StonithResource(klass=klass,
                               typename=typename,
                               pcmk_host_list=attr_dict['pcmk_host_list'],
                               ipaddr=attr_dict['ipaddr'],
                               login=attr_dict['login'],
                               passwd=attr_dict['passwd'])


class PacemakerClient:
    """
    Encapsulates the details of communication with Pacemaker via various
    CLI interfaces
    """

    def get_stonith_resources(self) -> List[Resource]:
        """Returns the list of all stonith resources in Pacemaker cluster"""

        def is_stonith(rsr: Resource) -> bool:
            match = re.match(r'^stonith:', rsr.resource_agent)
            return match is not None

        return [x for x in self._get_all_resources() if is_stonith(x)]

    def get_corosync_status(self) -> str:
        """
        Returns the output of 'pcs status corosync'. In case of non-zero
        exit code an exception will be thrown
        """

        # will raise an exception in case of non-zero exit code
        return self._execute(['pcs', 'status', 'corosync'])

    def get_stonith_resource_details(self,
                                     resource_name: str) -> StonithResource:
        """
        Returns detailed STONITH-specific information by the stonith
        resource name.
        """
        raw = self._get_stonith_resource_details_text(resource_name)
        return StonithParser().parse(raw)

    def _parse_xml(self, xml_str: str) -> Any:
        try:
            xml = ET.fromstring(xml_str)
            return xml
        except ET.ParseError:
            raise VError(EINVAL, 'Broken XML was given')

    def _get_full_status_xml(self) -> str:
        return self._execute(['pcs', 'status', '--full', 'xml'])

    def _get_status_text(self) -> str:
        return self._execute(['pcs', 'status'])

    def _get_stonith_resource_details_text(self, resource_name: str) -> str:
        return self._execute(['pcs', 'stonith', 'show', resource_name])

    def _get_all_resources(self) -> List[Resource]:
        xml_str = self._get_full_status_xml()
        xml = self._parse_xml(xml_str)

        def to_resource(tag):
            b = _to_bool
            return Resource(id=tag.attrib['id'],
                            resource_agent=tag.attrib['resource_agent'],
                            role=tag.get('role'),
                            target_role=tag.get('target_role'),
                            active=b(tag.attrib['active']),
                            orphaned=b(tag.attrib['orphaned']),
                            blocked=b(tag.attrib['blocked']),
                            managed=b(tag.attrib['managed']),
                            failed=b(tag.attrib['failed']),
                            failure_ignored=b(tag.attrib['failure_ignored']),
                            nodes_running_on=int(
                                tag.attrib['nodes_running_on']))

        result: List[Resource] = [
            to_resource(tag) for tag in xml.findall('./resources//resource')
        ]
        return result

    def _execute(self, cmd: List[str]) -> str:
        process = Popen(
            cmd,  # nosec
            stdin=PIPE,  # nosec
            stdout=PIPE,  # nosec
            stderr=PIPE,  # nosec
            encoding='utf8')  # nosec
        logging.debug('Issuing CLI command: %s', cmd)
        out, err = process.communicate()
        exit_code = process.returncode
        logging.debug('Finished. Exit code: %d', exit_code)
        if exit_code:
            raise VError(exit_code, err)
        return out


class PacemakerV:
    def __init__(self, executor: Optional[PacemakerClient] = None):
        self.executor = executor or PacemakerClient()

    def validate_two_stonith_only(self) -> None:
        """
        Ensures that Pacemaker cluster has exactly 2 stonith resources
        configured.
        """
        rsrc_list = self.executor.get_stonith_resources()
        count = len(rsrc_list)
        if count != 2:
            raise VError(
                ERANGE, 'Unexpected count of STONITH resources '
                f'found: {count}, expected: 2')

    def validate_stonith_for_both_nodes_exist(self) -> None:
        """
        Ensures that for every node in the cluster there is a stonith
        resource that can fence the node.
        """
        to_stonith = self.executor.get_stonith_resource_details
        resources = self.executor.get_stonith_resources
        stonith_list = [to_stonith(it.id) for it in resources()]
        node_names = set([it.pcmk_host_list for it in stonith_list])
        ok = 'srvnode-1' in node_names
        ok = ok and ('srvnode-2' in node_names)
        if not ok:
            raise VError(
                ERANGE, 'STONITH resources should manage both '
                'srvnode-1 and srvnode-2. Instead, the '
                f'following node names are found: {node_names}')

    def validate_all_stonith_running(self) -> None:
        """
        Ensures that all stonith resources are in running state. Note: if
        stonith parameters are incorrect, Pacemaker will not be able to
        start the resource.
        """
        rsrc_list = self.executor.get_stonith_resources()
        ok = all(r.active for r in rsrc_list)

        if not ok:
            raise VError(
                ERANGE, 'All STONITH resources were expected to be running. '
                f'Actual result: {rsrc_list}')

    def validate_configured(self):
        """
        Ensures that Pacemaker is running and that there are srvnode-1 and
        srvnode-2 configured in the cluster.
        """
        def is_node(line: str) -> bool:
            match = re.match(r'srvnode-[1,2]', line)
            return match is not None

        output = self.executor.get_corosync_status()
        nodes = [s for s in output.splitlines() if is_node(s)]
        if len(nodes) != 2:
            raise VError(
                ERANGE, 'Please ensure that both srvnode-1 and '
                'srvnode-2 are configured in Pacemaker')
