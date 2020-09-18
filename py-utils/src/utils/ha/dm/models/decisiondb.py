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

from schematics.types import StringType, DateTimeType

from cortx.utils.ha.dm.models.base import HAModel

class DecisionModel(HAModel):
    _id = "decision_id"

    decision_id = StringType()
    action = StringType()
    alert_time = DateTimeType()

    @staticmethod
    def create_decision_id(*decision_payload):
        """
        This method creates the key for Decision DB.
        :param decision_payload: Parameters for Decision Payload. :type: Tuple
        :return:
        """
        return "/".join(decision_payload)

    @staticmethod
    def instantiate_decision(**decision_payload):
        """
        Generate the Decision DB model object.
        :param decision_payload: Data For Decision DB.
        :return:
        """
        decision = DecisionModel()
        decision.decision_id = decision_payload.get("decision_id", "")
        decision.action = decision_payload.get("action", "")
        decision.alert_time = decision_payload.get("alert_time", "")
        return decision
