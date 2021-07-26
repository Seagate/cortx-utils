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
from cortx.utils.errors import BaseError


class BundleError(BaseError):

    def __init__(self, rc=None, desc=None, message_id=None, message_args=None):
        """Error class for support bundle related errors"""
        super(BundleError, self).__init__(
            rc, desc, message_id, message_args)

    def __str__(self):
        """returns bundle_error in formatted way"""
        return f"BundleError: {self._rc}: {self._desc}"