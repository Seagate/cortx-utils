# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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
from cortx.utils.schema import payload
from cortx.utils.log import Log
from cortx.utils.cli_framework.errors import ArgumentError

class CommonValidators:
    """
    Common Validators used for CLI
    """
    @staticmethod
    def _positive_int(value):
        try:
            if int(value) > -1:
                return int(value)
            raise ArgumentError(errno.EINVAL, "Value Must be Positive Integer")
        except ValueError:
            raise ArgumentError(errno.EINVAL,"Value Must be Positive Integer")

    @staticmethod
    def _file_parser(value):
        try:
            return payload.CommonPayload(value).load()
        except ValueError as ve:
            Log.error(f"File parsing failed. {value}: {ve}")
            raise ArgumentError(errno.EINVAL,
                ("File operations failed. "
                 "Please check if the file is valid or not"))
        except FileNotFoundError as err:
            Log.error(f"No such file present. {value}: {err}")
            raise ArgumentError(errno.ENOENT,
                ("File operation failed. "
                 "Please check if the file exists."))
        except KeyError as err:
            Log.error(f"Check file type. {value}: {err}")
            raise ArgumentError(errno.ENOENT,
                ("File operation failed. "
                 "Please check if the file exists and its type."))

