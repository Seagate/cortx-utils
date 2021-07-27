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

from cortx.utils.conf_store import Conf
from cortx.utils.shared_storage import SharedStorageError
from cortx.utils.shared_storage.shared_storage_agent import SharedStorageFactory

class Storage:

    """ Shared Storage Framework over various types of Shared Storages  """

    config_file = 'json:///etc/cortx/cortx.conf'

    def __init__(self):
        """ Initialize and load shared storage backend """

        Conf.load('config', Storage.config_file, skip_reload=True)
        shared_storage_type = Conf.get('config', 'shared_storage>type')
        shared_storage_path = Conf.get('config', 'shared_storage>path')
        if None in (shared_storage_type, shared_storage_path):
            raise SharedStorageError(errno.EINVAL, \
            "shared storage info not found in %s" % Storage.config_file)

        self.shared_storage_agent = SharedStorageFactory.get_instance( \
            shared_storage_type, shared_storage_path)

    @staticmethod
    def get_path():
        """ return shared storage mountpoint """
        storage = Storage()
        shared_path = storage.shared_storage_agent.get_path()
        return shared_path