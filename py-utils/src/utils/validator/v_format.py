#!/bin/env python3

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
from cortx.utils.validator.error import VError


class FormatV:
    """
    Format validators
    """
    @staticmethod
    def validate(value):
        try:
            return payload.CommonPayload(value).load()
        except ValueError:
            raise VError(errno.EINVAL,
                ("File operations failed. "
                 "Please check if the file is valid or not"))
        except FileNotFoundError:
            raise VError(errno.ENOENT,
                ("File operation failed. "
                 "Please check if the file exists."))
        except KeyError:
            raise VError(errno.ENOENT,
                ("File operation failed. "
                 "Please check if the file exists and its type."))
