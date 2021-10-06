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

from cortx.utils.common.common import CortxConf
cluster_conf = None
if not cluster_conf:
    cluster_conf = '/etc/cortx'
LOG_DIR = CortxConf.get_storage_path('log', cluster_conf=cluster_conf)
LOCAL_DIR = CortxConf.get_storage_path('local', cluster_conf=cluster_conf)
SB_DIR_LIST = [LOG_DIR, LOCAL_DIR]
SUPPORT_BUNDLE_TAG = 'support_bundle;'
SUPPORT_BUNDLE = 'SUPPORT_BUNDLE'
SOS_COMP = 'os'
SB_COMPONENTS = 'components'
SB_COMMENT = 'comment'
SB_NODE_NAME = 'node_name'
SB_BUNDLE_ID = 'bundle_id'
SB_BUNDLE_PATH = 'bundle_path'
SB_SYMLINK_PATH = 'symlink_path'
SYMLINK_PATH = '/tmp/support_bundle/'
FILESTORE_PATH = '/tmp/sb_status.json'
SB_INDEX = 'sb_index'
PERMISSION_ERROR_MSG = "Failed to cleanup {path} due to insufficient permissions"
