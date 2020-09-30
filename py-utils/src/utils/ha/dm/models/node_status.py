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

from schematics.types import IntType, StringType

from cortx.utils.ha.dm.models.base import HAModel


class NodeStatusModel(HAModel):
    _id = "node_id"

    node_id = StringType()
    io_failure_count = IntType()
    management_failure_count = IntType()

    @staticmethod
    def create_model_obj(node_id, **status_payload):
        """
        Create Model Object for Node Status Model

        :param node_id: Node Id :type: Str
        :param status_payload: Payload or remaining keys for Model :type: Dict
        :return: Model Object :type: NodeStatusModel
        """

        node_status = NodeStatusModel()
        node_status.node_id = node_id
        node_status.io_failure_count = status_payload.get('io_failure_count', 0)
        node_status.management_failure_count = status_payload.get('management_failure_count', 0)
        return node_status
