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

import errno
import re
from typing import List, NamedTuple, Optional

from cortx.utils.process import SimpleProcess
from cortx.utils.validator.error import VError


class ServiceInfo(NamedTuple):
    """Structure for storing service status"""
    status: str
    name: str


class HaStatusV:
    """HA related validations."""

    def validate_io_stack_sane(self):
        """
        Ensures that there is no anomaly in Cortx IO stack.
        """

        self._ensure_hctl_available()
        status_str = self._get_hctl_status()
        services = self._extract_service_info(status_str)

        if not services:
            raise VError(
                errno.EINVAL, "No services could be seen in hctl "
                "status output. Either the cluster is not configured or "
                "the output was not understood. In any case, the cluster "
                "doesn't look sane.")
        io_service_names = {'m0_client', 'ioservice'}
        data_services = [
            srv for srv in services if srv.name in io_service_names
        ]
        if any(srv.status == 'unknown' for srv in data_services):
            raise VError(
                errno.EINVAL,
                f"Some of IO services don't look sane: {data_services}")

    def _extract_service_info(self, raw_text: str) -> List[ServiceInfo]:
        result = []
        for line in raw_text.splitlines():
            # match line as follows:
            #     [started]  hax        0x7200000000000001:0x6  ...
            match = re.match(r'[\s]+\[([^\]]*)\]\s+([^\s]+).*$', line)
            if not match:
                continue
            (status, name) = (match.group(1), match.group(2))
            result.append(ServiceInfo(name=name, status=status))
        return result

    def _ensure_hctl_available(self) -> None:
        self._execute(['hctl', '--help'],
                      'Failed to invoke hctl. Is Hare component installed?')

    def _get_hctl_status(self) -> str:
        return self._execute(['hctl', 'status'])

    def _execute(self,
                 args: List[str],
                 error_text: Optional[str] = None) -> str:
        out, err, exitcode = SimpleProcess(args).run()
        out = out.decode("utf-8")
        err = err.decode("utf-8")
        error_text = error_text or err
        if exitcode:
            raise VError(errno.EINVAL, error_text)
        return out
