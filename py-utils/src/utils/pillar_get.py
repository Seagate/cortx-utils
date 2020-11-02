#!/usr/bin/env python3

#
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
#

import json

from cortx.utils.process import SimpleProcess


class PillarGet():

    @staticmethod
    def get_pillar(key):
        """ Get pillar data for key. """
        cmd = f"salt-call pillar.get {key} --out=json"
        cmd_proc = SimpleProcess(cmd)
        run_result = list(cmd_proc.run())

        if run_result[2] == 127:
            run_result[0] = "salt-call: command not found"
        elif run_result[2] == 0:
            res = json.loads(run_result[0])
            res = res['local']
            if not res:
                run_result[0] = f"No pillar data for key: {key}"
                run_result[1] = f"No pillar data for key: {key}"
                run_result[2] = 1
            else:
                run_result[0] = res
        else:
            run_result[0] = "Failed to get pillar data"

        return run_result


    @staticmethod
    def get_hostnames():
        """Get hostnames from pillar data."""
        res = PillarGet.get_pillar("cluster:node_list")
        if res[2]:
            return res
        hostnames = []
        for node in res[0]:
            res = PillarGet.get_pillar(f"cluster:{node}:hostname")
            if res[2]:
                return res
            hostnames.append(res[0])
        res[0] = hostnames
        return res
