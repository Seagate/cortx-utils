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

from cortx.utils.cli_framework.errors import CliError
import errno


class ArgType:
    """
    Base class for Argumentent type validaton
    """
    @staticmethod
    def validate(val):
       raise CliError(errno.ENOSYS, "validate not implemented")

class IntType(ArgType):
    """
    Integer type argument validation
    """
    @staticmethod
    def validate(value):
        try:
            if int(value) > -1:
                return int(value)
            raise CliError(errno.EINVAL, "Value Must be Positive Integer")
        except ValueError:
            raise CliError(errno.EINVAL,"Invalid argument.")
