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

import errno
import os

from cortx.utils.log import Log
from cortx.utils.schema.payload import JsonMessage, Json
from cortx.utils import const
from cortx.utils.ha.dm.repository.decisiondb import DecisionDB

class RuleEngine(object):
    """Module responsible for validating the alert against set of rules."""

    def __init__(self, rule_file=None):
        self._rule_file = rule_file
        self._rules_schema = None
        self._load_rules()

    def _load_rules(self):
        """
        Reads the json structured rule data from the file, and returns it.

        in dict format.
        """
        rules_data = None
        try:
            if self._rule_file is None:
                return None
            Log.debug(f"Loading rules json into memory. File: {self._rule_file}")
            with open(self._rule_file, 'r') as fp:
                rules_data = fp.read()
            if rules_data:
                rules_json = JsonMessage(rules_data)
                self._rules_schema = rules_json.load()
        except OSError as os_error:
            if os_error.errno == errno.ENOENT:
                Log.error(f'File {self._rule_file} does not exist')
            elif os_error.errno == errno.EACCES:
                Log.error(f'Not enough permission to read {self._rule_file} file')
            else:
                Log.error(f'Error while reading from file {self._rule_file}')

    def evaluate_alert(self, alert):
        """
        Compares the alert with the predefined json structure and returns.

        action such as fail-over, fail-back etc.
        """
        Log.debug(f"Evaluating alert: {alert}")
        action = None
        component_var = ""
        module_var = ""
        if not self._rules_schema:
            return action
        sensor_response = alert.get(const.MESSAGE).get(const.SENSOR_RES_TYPE)
        res_type = sensor_response.get(const.INFO).get(const.RESOURCE_TYPE)
        if res_type is None:
            return action
        alert_type = sensor_response.get(const.ALERT_TYPE)
        severity = sensor_response.get(const.SEVERITY)
        # In case of IEM alerts for fetching the rules we will have to make use
        # of two additional fields:
        # 1. component_id
        # 2. module_id
        if res_type == const.IEM:
            component_var = sensor_response.get(const.SPECIFIC_INFO).get\
                (const.SPECIFIC_INFO_COMPONENT)
            module_var = sensor_response.get(const.SPECIFIC_INFO).get\
                (const.SPECIFIC_INFO_MODULE)
        res_type_data = self._rules_schema[res_type]
        if res_type_data is not None:
            for item in res_type_data:
                if alert_type == item[const.ALERT_TYPE] and\
                    severity == item[const.SEVERITY]:
                    if res_type == const.IEM:
                        if component_var == item[const.COMPONENT_ID] and\
                            module_var == item[const.MODULE_ID]:
                            action = item[const.ACTION]
                    else:
                        action = item[const.ACTION]
        Log.debug(f"Found {action} action for resource: {res_type} with alert type:\
            {alert_type} and severity: {severity}.")
        return action

class DecisionMaker(object):
    """
    This class is responsible for taking the HA decisions.

    such as failover/failback with the help of RuleEngine.
    """

    def __init__(self, decisiondb=DecisionDB()):
        self._rule_engine = RuleEngine(os.path.join(\
            const.CORTX_HA_INSTALL_PATH, const.RULES_FILE_PATH))
        self._decision_db = decisiondb
        self._conf = Json(os.path.join(\
            const.CORTX_HA_INSTALL_PATH, const.CONF_FILE_PATH)).load()

    async def _get_data_nw_interface(self, host_id):
        interface = []
        if self._conf:
            interface = self._conf.get(const.NETWORK).get(host_id).get\
                (const.DATA_IFACE)
        return interface

    async def _get_mgmt_nw_interface(self, host_id):
        interface = []
        if self._conf:
            interface = self._conf.get(const.NETWORK).get(host_id).get\
                (const.MGMT_IFACE)
        return interface

    async def _get_host_id(self, node_id):
        host_id = ""
        if self._conf:
            host_id = self._conf.get(const.NODES).get(node_id)
        return host_id

    async def handle_alert(self, alert):
        """
        Accepts alert in the dict format and validates the same.

        alert against set of rules with the help of RuleEngine.
        """
        try:
            if alert is not None:
                action = self._rule_engine.evaluate_alert(alert)
                if action is not None:
                    await self._store_action(alert, action)
        except Exception as e:
            Log.error(f"Error occured during alert handling. {e}")

    async def _store_action(self, alert, action):
        """
        Further parses the alert to store information such as.

        component: Actual Hw component which has been affected
        component_id: FRU_ID
        entity: enclosure/node
        entity_id: resource id
        """
        try:
            sensor_response = alert.get(const.MESSAGE).get(const.SENSOR_RES_TYPE)
            info_dict = await self._set_db_key_info(sensor_response)
            if info_dict:
                await self._decision_db.store_event(info_dict[const.ENTITY],\
                    info_dict[const.ENTITY_ID], info_dict[const.COMPONENT],\
                    info_dict[const.COMPONENT_ID], info_dict[const.EVENT_TIME], action)
        except Exception as e:
            Log.error(f"Error occured during storing action. {e}")

    async def _set_db_key_info(self, sensor_response):
        """
        This function derives entity, entity_id, component, component_id,
        event_time from the incoming alert.

        These fields are required to create key for storing the decision in db.
        Key format -
        HA/entity/entity_id/component/component_Id/timestamp
        Examples -
        1. HA/Enclosure/0/controller/1/timestamp
        2. HA/Enclosure/0/controller/2/timestamp
        3. HA/Enclosure/0/fan/0/timestamp
        4. HA/Node/1/raid/0/timestamp
        5. HA/Node/0/IEM/motr/timestamp
        6. HA/Node/1/IEM/s3/timestamp
        """
        info_dict = dict()
        info = sensor_response.get(const.INFO)
        resource_type = info.get(const.RESOURCE_TYPE)
        resource_id = info.get(const.RESOURCE_ID)
        node_id = info.get(const.NODE_ID)
        host_id = await self._get_host_id(node_id)
        # Setting event time.
        info_dict[const.EVENT_TIME] = info.get(const.EVENT_TIME)

        # Here resource type can be in 2 forms -.

        # 1. enclosure:fru:disk, node:os:disk_space, node:interface:nw:cable etc
        # 2. enclosure, iem
        # Spliting the resource type will give us the entity and component fields.

        res_list = resource_type.split(':')

        # 2. Setting entity.
        # For IEM alerts we do not get Node/Enclosure in resource type, so we
        # have to hardcode it to node.

        if resource_type == const.IEM:
            component_var = sensor_response.get(const.SPECIFIC_INFO).get\
                (const.SPECIFIC_INFO_COMPONENT)
            info_dict[const.ENTITY] = const.NODE
            info_dict[const.COMPONENT] = resource_type
            info_dict[const.COMPONENT_ID] = component_var
        else:
            info_dict[const.ENTITY] = res_list[0]

        # 3. Setting entity_id
        if info_dict[const.ENTITY] == const.NODE:
            info_dict[const.ENTITY_ID] = host_id
        else:
            info_dict[const.ENTITY_ID] = "0"

        # 4. Setting Component.
        # We will check if we have got the component value in resource type.
        if len(res_list) > 1:
            info_dict[const.COMPONENT] = res_list[len(res_list) - 1]
        else:
            # We have to perform some checks if component is not present in.

            # reource_type field.
            # 1. For storage connectivity we have component = connectivity
            # 2. For storage connectivity we have component_id = node/host id
            if info_dict[const.ENTITY] == const.ENCLOSURE:
                info_dict[const.COMPONENT] = const.CONNECTIVITY
                info_dict[const.COMPONENT_ID] = host_id

        # 5. Setting component id
        if info_dict[const.COMPONENT] == const.CONTROLLER:
            info_dict[const.COMPONENT_ID] = host_id
        elif resource_type in (const.NIC, const.NIC_CABLE):
            # If resource_type is node:interface:nw, node:interface:nw:cable.

            # then we will read the values from config to know whether it is
            # data or management interface.
            # Since BMC interface is also included in NIC alert we do not have to
            # take any against against it.
            # In case we found the interface related to BMC so we will ignore it.
            comp_id = await self._get_component_id_for_nic(host_id, resource_id)
            if comp_id:
                info_dict[const.COMPONENT_ID] = comp_id
            else:
                info_dict = {}
        elif resource_type not in (const.IEM, const.ENCLOSURE):
            # For IEM the component id is fetched from specific info's component.

            # id field
            info_dict[const.COMPONENT_ID] = resource_id

        return info_dict

    async def _get_component_id_for_nic(self, host_id, resource_id):
        component_id = ""
        # First checking if resource is found in data_nw.
        nw_interface = await self._get_data_nw_interface(host_id)
        if resource_id in nw_interface:
            component_id = const.DATA
        else:
            # Since resource not found in data_nw lets serach is mgmt_nw.
            nw_interface = await self._get_mgmt_nw_interface(host_id)
            if resource_id in nw_interface:
                component_id = const.MGMT
        return component_id
