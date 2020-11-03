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
from errno import ERANGE
from subprocess import PIPE, Popen  # nosec
from typing import List, Optional

from .error import VError


class CliExecutor:
    def get_full_status_xml(self) -> str:
        return self._execute(['pcs', 'status', '--full', 'xml'])

    def get_status_text(self) -> str:
        return self._execute(['pcs', 'status'])

    def get_stonith_resource_details(self, resource_name: str) -> str:
        return self._execute(['pcs', 'stonith', 'show', resource_name])

    def get_corosync_status(self) -> str:
        # will raise an exception in case of non-zero exit code
        return self._execute(['pcs', 'status', 'corosync'])

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


class PacemakerHealth:
    def __init__(self, executor: Optional[CliExecutor] = None):
        self.executor = executor or CliExecutor()

    def ensure_configured(self):
        def is_node(line: str) -> bool:
            match = re.match(r'srvnode-[1,2]', line)
            return match is not None

        output = self.executor.get_corosync_status()
        nodes = [s for s in output.splitlines() if is_node(s)]
        if len(nodes) != 2:
            raise VError(
                ERANGE, 'Please ensure that both srvnode-1 and '
                'srvnode-2 are configured in Pacemaker')
