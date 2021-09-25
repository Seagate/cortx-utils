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
import os

from cortx.utils.conf_store import Conf
from cortx.utils.shared_storage import SharedStorageError
from cortx.utils.shared_storage.shared_storage_agent import SharedStorageFactory
from cortx.utils.common import CortxConf

class Storage:

    """ Shared Storage Framework over various types of Shared Storages  """

    def __init__(self):
        """ Initialize and load shared storage backend """

        self.shared_storage_url = CortxConf.get_key('support>shared_path')
        if self.shared_storage_url is not None:
            self.shared_storage_agent = SharedStorageFactory.get_instance( \
                self.shared_storage_url)

    @staticmethod
    def get_path(name: str = None, exist_ok: bool = True) -> str:
        """ return shared storage mountpoint """

        storage = Storage()
        if storage.shared_storage_url is None:
            return None

        shared_path = storage.shared_storage_agent.get_path()
        if name:
            try:
                spec_path = os.path.join(shared_path, name)
                os.makedirs(spec_path, exist_ok = exist_ok)
                shared_path = spec_path
            except OSError as e:
                raise SharedStorageError(errno.EINVAL, \
                    "dir already exists, (use exist_ok as True) %s" % e)

        return shared_path