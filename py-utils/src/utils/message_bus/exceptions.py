#!/usr/bin/env python3

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


from src.utils.errors import BaseError

KEY_NOT_FOUND_ERROR = 0x1020
CLIENT_NOT_FOUND_ERROR = 0x1021

class ClientNotfoundError(BaseError):
    def __init__(self, desc=None, message_id=None, message_args=None):
        super().__init__(CLIENT_NOT_FOUND_ERROR, 'Exception : Client Not Found Error')


class KeyNotFoundError(BaseError):
    def __init__(self, desc=None, message_id=None, message_args=None):
        super().__init__(KEY_NOT_FOUND_ERROR, 'Exception : Key Not Found Error')