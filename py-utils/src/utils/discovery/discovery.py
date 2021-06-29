#!/bin/python3

# CORTX Python common library.
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

import errno
import threading
import time

from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.discovery.node_health import NodeHealth


class Discovery:
    """Common interfaces of Discovery Library"""

    @staticmethod
    def generate_node_health(rpath: str = None, store_url: str = None):
        """
        Generates node resource map and health information. This returns
        unique id for any accepted request.

        rpath: Resource path in resource map to fetch its health.
            If rpath is not given, it will fetch whole Cortx Node
            data health.
            Examples:
                node>compute[0]>hw>disks
                node>compute[0]
                node>storage[0]
                node>storage[0]>hw>psus
        store_url: Path to store resource health information
        """
        request_id = str(time.time()).replace(".", "")
        t = threading.Thread(
            target=NodeHealth.generate, args=(rpath, request_id, store_url))
        t.start()

        # When multiple requests gets registered, KV load throws decoding error
        # due to key scanning happening at the same time by other requests.
        time.sleep(0.5)

        return request_id

    @staticmethod
    def get_gen_node_health_status(request_id):
        """
        Returns processing status of the given request id.

        "In-progress" if health generation request is being processed
        "Success" if health generation request is completed
        "Failed (with reason)" if request is failed
        """
        if not request_id:
            raise DiscoveryError(errno.EINVAL, "Invalid request ID.")
        return NodeHealth.get_processing_status(request_id)

    @staticmethod
    def get_node_health(request_id=None):
        """
        Returns resource health map backend URL.

        request_id: Unique ID returned by generate node health method
        If request_id is not given, this will return available static
        store url.
        URL format: "json://<file_path>/<file_name>"
        """
        return NodeHealth.get_resource_map_location(request_id)
