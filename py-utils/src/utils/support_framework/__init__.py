#!/usr/bin/env python3

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

from cortx.utils.support_framework.bundle import Bundle
from cortx.utils.support_framework.support_bundle import SupportBundle
# adds all above defined packages in import *
__all__ = ('Bundle', 'SupportBundle')

from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.log import Log

Conf.load('cortx_config', 'json:///etc/cortx/cortx.conf')
log_level = Conf.get('cortx_config', 'utils>log_level', 'INFO')
Log.init('support_bundle', '/var/log/cortx/utils/support', level=log_level, \
    backup_count=5, file_size_in_mb=5)
