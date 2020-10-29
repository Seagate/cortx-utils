#!/bin/python3

# CORTX Python common library.
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

import json
import errno
from cortx.utils.store.dstore import KvDB
from cortx.utils.store.error import KvError
from cortx.utils.process import SimpleProcess


class PillarDB(KvDB):
    """ Salt Pillar based KV Store """

    def __init__(self):
        super(PillarDB, self).__init__()

    def get(self, key):
        """Get pillar data for key."""

        cmd = f"salt-call pillar.get {key} --out=json"
        cmd_proc = SimpleProcess(cmd)
        out, err, rc = cmd_proc.run()

        if rc != 0:
            msg = "get: salt-call: command not found" if rc == 127 else \
                "get-pillar: Failed to get pillar data"
            raise KvError(rc, msg)

        res = json.loads(out)
        res = res['local']

        if not res:
            raise KvError(errno.ENOENT, f"get: No pillar data for {key}.")

        return res

    def set(self, key, value):
        # TODO: Implement
        pass
