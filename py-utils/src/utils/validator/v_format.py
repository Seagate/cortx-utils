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
from cortx.utils.log import Log
from cortx.utils.validator.error import VError


class FormatV:
    """
    Format validators
    """

    def validate(self, v_type, value):
        if v_type == "positive_int":
            FormatV._validate_positive_int(value)
        elif v_type == "file_format":
            FormatV._validate_file_format(value)

    @staticmethod
    def _validate_positive_int(value):
        """
        Checks for positive int else raise Error
        """
        try:
            if int(value) > -1:
                return int(value)
            raise VError(errno.EINVAL, "Value Must be Positive Integer")
        except ValueError:
            raise VError(errno.EINVAL,"Invalid argument.")

    @staticmethod
    def _validate_file_format(value):
        try:
            return payload.CommonPayload(value).load()
        except ValueError as ve:
            raise VError(errno.EINVAL,
                ("File operations failed. "
                 "Please check if the file is valid or not"))
        except FileNotFoundError as err:
            raise VError(errno.ENOENT,
                ("File operation failed. "
                 "Please check if the file exists."))
        except KeyError as err:
            raise VError(errno.ENOENT,
                ("File operation failed. "
                 "Please check if the file exists and its type."))

