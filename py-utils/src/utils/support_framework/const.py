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

DEFAULT_CORTX_CONF= 'yaml:///etc/cortx/cluster.conf'
SB_PATH = '/var/cortx/support_bundle'
SUPPORT_YAML = 'cortx/utils/conf/support_bundle.yaml'
SUPPORT_BUNDLE_TAG = 'support_bundle;'
SUPPORT_BUNDLE = 'SUPPORT_BUNDLE'
SOS_COMP = 'os'
SB_COMPONENTS = 'components'
SB_COMMENT = 'comment'
SB_NODE_NAME = 'node_name'
SB_BUNDLE_ID = 'bundle_id'
SB_BUNDLE_PATH = 'bundle_path'
SB_DURATION = 'duration'
SB_SIZE = 'size_limit'
SB_SYMLINK_PATH = 'symlink_path'
SYMLINK_PATH = '/tmp/support_bundle/'
FILESTORE_PATH = f'{SB_PATH}/sb_status.json'
SB_INDEX = 'sb_index'
CORTX_SOLUTION_DIR = '/etc/cortx/solution'
CORTX_RELEASE_INFO = '/opt/seagate/cortx/RELEASE.INFO'
PERMISSION_ERROR_MSG = "Failed to cleanup {path} due to insufficient permissions"
