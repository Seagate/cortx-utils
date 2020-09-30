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

BUILD_PATH = "/tmp"
BASE_PATH = '/opt/seagate/cortx/ha/'
CONF_PATH = '/etc/cortx/ha/'
PROV_CONF_INDEX = "PROV_CONF_INDEX"
HAC_LOG = "/tmp/hac.log"
HA_MODES = ["active_passive", "active_active", "primary_secondary"]
HA_GROUP = ["common", "management", "io"]
IO_PATH = 'io'
MGMT_PATH = 'mgmt'
FAILED_STATUSES = ['failed']
DECISION_MAPPING_FILE = 'decision_monitor_conf.json'
HA_DATABASE_SCHEMA = 'database.json'
