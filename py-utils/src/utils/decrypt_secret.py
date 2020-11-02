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

from cortx.utils.process import SimpleProcess


def decrypt_secret(enc_key, secret):
    """ Decrypt secret value for User.
    """

    cmd = f"salt-call lyveutil.decrypt {enc_key} {secret} --output=newline_values_only"
    cmd_proc = SimpleProcess(cmd)
    run_result = list(cmd_proc.run())

    if run_result[2] == 127:
        run_result[0] = "salt-call: command not found"

    elif run_result[2] == 0:
        run_result[0] = run_result[0].strip()
        if not run_result[0]:
            run_result[0] = f"Could not decrypt secret data: '{secret}'"
            run_result[2] = 1

    return run_result
