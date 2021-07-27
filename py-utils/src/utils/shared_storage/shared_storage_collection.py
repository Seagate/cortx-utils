# CORTX Python common library.
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

from cortx.utils.shared_storage import SharedStorageAgent
from cortx.utils.shared_storage import SharedStorageError

class GlusterSharedStorage(SharedStorageAgent):

    """ GlusterFS based shared storage implementation """

    name = "GlusterFS"

    def __init__(self, shared_path: str  = ""):
        """ Construct an object for GlusterSharedStorage class """
        self.shared_path = shared_path

    def _fetch_path(self):
        """ fetch path from confstore """
        shared_path = self.shared_path

        if not shared_path:
            raise SharedStorageError(errno.EINVAL, \
                "shared_path not found!")
        return shared_path
