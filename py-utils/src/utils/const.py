#!/usr/bin/python3.6

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

CLUSTER_CONF = 'yaml:///etc/cortx/cluster.conf'
GCONF_INDEX = 'config'
#GCONF KEYS
CLUSTER_CONF_LOG_KEY = 'cortx>common>storage>log'
MSG_BUS_BACKEND_KEY = 'cortx>utils>message_bus_backend'
EXTERNAL_KEY = 'cortx>external'
#DELTA KEYS
DELTA_INDEX = 'gconf_change_set'
CHANGED_PREFIX = 'changed>'
NEW_PREFIX = 'new>'
DELETED_PREFIX = 'deleted>'

DEFAULT_INSTALL_PATH = '/opt/seagate'
CORTX_HA_INSTALL_PATH = "/etc/cortx/ha/"
RULES_FILE_PATH = "rules_engine_schema.json"
CONF_FILE_PATH = "decision_monitor_conf.json"
MESSAGE = "message"
SENSOR_RES_TYPE = "sensor_response_type"
INFO = "info"
RESOURCE_TYPE = "resource_type"
ALERT_TYPE = "alert_type"
SEVERITY = "severity"
ACTION = "action"
RESOURCE_ID = "resource_id"
NODE_ID = "node_id"
EVENT_TIME = "event_time"
ENCLOSURE = "enclosure"
ENTITY = "entity"
ENTITY_ID = "entity_id"
COMPONENT = "component"
COMPONENT_ID = "component_id"
SPECIFIC_INFO_COMPONENT = "component"
CONNECTIVITY = "connectivity"
NIC = "node:interface:nw"
SPECIFIC_INFO = "specific_info"
IEM = "iem"
NODE = "node"
PILLAR_GET = "pillar.get"
CLUSTER = "cluster"
NETWORK = "network"
DATA = "data"
MGMT = "mgmt"
DATA_IFACE = "data_iface"
MGMT_IFACE = "mgmt_iface"
HOST_ID = "host_id"
NODES = "nodes"
CONTROLLER = "controller"
MODULE_ID = "module_id"
SPECIFIC_INFO_MODULE = "module"
NIC_CABLE = "node:interface:nw:cable"
UNSUPPORTED_FEATURE = "UNSUPPORTED_FEATURE"
SERIAL_NO_FILE_PATH = "/opt/seagate/lr-serial-number"
ITEMS_SEPARATOR = ", "
STORAGE_ENCLOSURE = "storage_enclosure"
CLUSTER_ID = "cluster_id"
CONSUL_CONF = "/etc/cortx/consul_conf"
RELEASE_KEY = "cortx>common>release"
RELEASE_NAME_KEY = RELEASE_KEY + ">name"
RELEASE_VERSION_KEY  = RELEASE_KEY + ">version"
NUM_STORAGESET_KEY = "cluster>num_storage_set"
STORAGE_SET = "cluster>storage_set[%s]"
NUM_NODES_KEY = STORAGE_SET + ">num_nodes"
NODE_ID_KEY = STORAGE_SET + ">nodes[%s]"
NODE_NAME_KEY = "node>%s>name"
NUM_COMPONENTS_KEY = "node>%s>num_components"
COMPONENT_KEY = "node>%s>components[%s]"
COMPONENT_NAME_KEY = COMPONENT_KEY + ">name"
COMPONENT_VERSION_KEY = COMPONENT_KEY + ">version"
# Mapping of cortx conf component names to RELEASE.INFO component names
COMPONENT_NAME_MAP = {'CORTX': 'CORTX', 'cortx-motr': 'motr', 'cortx-rgw': 'rgw',
                    'cortx-hare': 'hare', 'cortx-py-utils': 'utils', 'cortx-csm_agent': 'csm',
                    'cortx-ha': 'ha', 'cortx-prvsnr': 'prvsnr'}
VERSION_UPGRADE = "UPGRADE"

# Distributed Session Lock related keys
LOCK_KEY = "cortx>lock>locked_time"
