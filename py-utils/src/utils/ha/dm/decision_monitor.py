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

import asyncio
import os
import traceback
from typing import AnyStr

from cortx.utils.data.access import SortBy, SortOrder
from cortx.utils.ha.dm.actions import Action
from cortx.utils.ha.dm.models.decisiondb import DecisionModel
from cortx.utils.ha.dm.repository.decisiondb import DecisionDB
from cortx.utils.ha.hac import const
from cortx.utils.log import Log
from cortx.utils.schema.payload import Json


class DecisionMonitor:

    """Fetch Resource Decisions from Decision DB."""
    def __init__(self):
        self._resource_file = Json(
            os.path.join(const.CONF_PATH, const.DECISION_MAPPING_FILE)).load()
        self._loop = asyncio.get_event_loop()
        self._consul_call = self.ConsulCallHandler(self._resource_file)

    class ConsulCallHandler:

        """Handle async call to consul."""
        def __init__(self, resource_file):
            """Initialize consul call handler."""
            self._decisiondb = DecisionDB()
            self._consul_timeout = resource_file.get("request_timeout", 3.0)

        async def get(self, **resource_key):
            """Get consul data else raise error."""
            return await asyncio.wait_for(
                self._decisiondb.get_event_time(
                    **resource_key, sort_by=SortBy(DecisionModel.alert_time, SortOrder.DESC)),
                timeout=self._consul_timeout)

        async def delete(self, **resource_key):
            """Delete consul data else raise error."""
            await asyncio.wait_for(
                self._decisiondb.delete_event(**resource_key), timeout=self._consul_timeout)

    def get_resource_status(self, resource: AnyStr):
        """
        Get the status for the resource

        :param resource: Name of the resource
        """

        Log.debug(f"Received Status Request for resource {resource}")
        resource_key = self._resource_file.get("resources", {}).get(resource, {})
        try:
            resource_data = self._loop.run_until_complete(self._consul_call.get(**resource_key))
        except Exception as e:
            # Return OK if Failed to Fetch Resource Status.
            Log.error(f"{traceback.format_exc()} {e}")
            return Action.OK
        if resource_data:
            return resource_data[0].action
        return Action.OK

    def get_resource_group_status(self, resource_group):
        """
        Fetch Resource Group Status.

        :param resource_group: Name of Resource Group.
        """

        group_status = []
        Log.debug(f"Received Status Request for resource group {resource_group}")
        # Fetch List of Resources in group
        resources = self._resource_file.get("resource_groups", {}).get(resource_group, [])
        for resource in resources:
            # Check's the status for each resource.
            status = self.get_resource_status(resource)
            if status in [Action.FAILED]:
                # Return Failed if any one is Failed Status in RG.
                return status
            group_status.append(status)
        if Action.RESOLVED in group_status:
            #  Return Resolved if none is Failed and any one is resolved Status in RG.
            return Action.RESOLVED
        return Action.OK

    def acknowledge_resource(self, resource, force=False):
        """Acknowledge a Single Resource Group."""
        Log.debug(f"Received Acknowledge Request for resource {resource}")
        resource_key = self._resource_file.get("resources", {}).get(resource, {})
        try:
            if force or self.get_resource_status(resource) != Action.FAILED:
                self._loop.run_until_complete(self._consul_call.delete(**resource_key))
        except Exception as e:
            Log.error(str(e))

    def acknowledge_resource_group(self, resource_group):
        """Acknowledge a Single Resource Group."""
        Log.debug(f"Received Acknowledge Request for resource group {resource_group}")
        resources = self._resource_file.get("resource_groups", {}).get(resource_group, [])
        for resource in resources:
            self.acknowledge_resource(resource)
