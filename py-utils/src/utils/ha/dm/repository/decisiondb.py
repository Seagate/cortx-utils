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

from cortx.utils import const as general_const
from cortx.utils.common import DbConf
from cortx.utils.data.access import Query
from cortx.utils.data.access.filters import Compare
from cortx.utils.data.db.db_provider import DataBaseProvider, GeneralConfig
from cortx.utils.ha.dm.models.decisiondb import DecisionModel
from cortx.utils.log import Log

class DecisionDB:
    """
    Encapsulates decision management activities.

    This is intended to be used during decision management
    """

    def __init__(self) -> None:
        """Init load consul db for storing key in db."""
        DbConf.init(general_const.CLUSTER_CONF)
        dict_conf = DbConf.export_database_conf()
        conf = GeneralConfig(dict_conf)
        self.storage = DataBaseProvider(conf)

    async def store_event(self, entity, entity_id, component, component_id,
                          alert_time, action):
        """
        Stores Data in Decision DB in Consul.

        :param entity: Entity Name :type: Str
        :param entity_id: Entity Id :type: Str
        :param component: Component Name :type: Str
        :param component_id: Component Id :type: Str
        :param alert_time: Alert Generated time :type: Str
        :param action: Action for the Component :type: Str
        :return:
        """
        # Generate Key
        decision_id = DecisionModel.create_decision_id(entity, entity_id,
                                                       component, component_id,
                                                       alert_time)
        Log.debug(f"Loading event for {decision_id} Action:- {action}")
        # Generate Decision DB Object.
        decision = DecisionModel.instantiate_decision(decision_id=decision_id,
                                                      action=action,
                                                      alert_time=alert_time)
        # Save Data.
        await self.storage(DecisionModel).store(decision)

    async def get_event(self, entity, entity_id, component, component_id,
                        alert_time):
        """
        Get a event with specific time.

        :param entity: Entity Name :type: Str
        :param entity_id: Entity Id :type: Str
        :param component: Component Name :type: Str
        :param component_id: Component Id :type: Str
        :param alert_time: Alert Generated time :type: Str
        :return: action For Respective Alert :type: Str
        """
        # Generate Key
        decision_id = DecisionModel.create_decision_id(entity, entity_id,
                                                       component, component_id,
                                                       alert_time)
        Log.debug(f"Fetch event for {decision_id}")
        # Create Query
        query = Query().filter_by(
            Compare(DecisionModel.decision_id, '=', decision_id))
        return await self.storage(DecisionModel).get(query)

    async def get_event_time(self, entity, entity_id, component, component_id,
                             **kwargs):
        """
        Fetch All Event with All Components Name.

        :param entity: Entity Name :type: Str
        :param entity_id: Entity Id :type: Str
        :param component: Component Name :type: Str
        :param component_id: Component Id :type: Str
        :return:
        """
        # Generate Key
        decision_id = DecisionModel.create_decision_id(entity, entity_id,
                                                       component, component_id)
        Log.debug(f"Fetch event time for {decision_id}")
        # Create Query
        query = Query().filter_by(
            Compare(DecisionModel.decision_id, 'like', decision_id))

        if kwargs.get("sort_by"):
            query.order_by(kwargs["sort_by"].field, kwargs['sort_by'].order)

        return await self.storage(DecisionModel).get(query)

    async def delete_event(self, entity, entity_id, component, component_id):
        """
        Delete all Component Related Events.

        :param entity: Entity Name :type: Str
        :param entity_id: Entity Id :type: Str
        :param component: Component Name :type: Str
        :param component_id: Component Id :type: Str
        :return:
        """
        # Generate Key
        decision_id = DecisionModel.create_decision_id(entity, entity_id,
                                                       component, component_id)
        Log.debug(f"Deleting event for {decision_id}")
        # Delete all the Decisions Related to The Event.
        await self.storage(DecisionModel).delete(
            Compare(DecisionModel.decision_id, 'like', decision_id))
