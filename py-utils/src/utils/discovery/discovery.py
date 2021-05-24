#!/bin/python3

# CORTX Python common library.
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
import json
import os

from cortx.utils.discovery.node_health_generator import NodeHealthGenerator
from cortx.utils.discovery.error import DiscoveryError


class Discovery:
    """A common interface of node health generator."""

    PROCESSING = "processing"
    SUCCESSFUL = "success"

    def __init__(self):
        self.gen_marker = "/tmp/dm_inprogress"

    def generate_node_health(self, rpath:str=None):
        """This method generates node resource map and health information.

        Health information will be stored in Fs and therefore it fetches
        health information for given rpath later through show command.
        """
        status = self.get_gen_node_health_status()
        if status != self.PROCESSING:
            # TODO: Start asynchronous tasks on collecting node health information
            NodeHealthGenerator.run()

            # If no previous request is processing or pending, then accept
            # incoming request and acknowledge back.
            status = self.PROCESSING
        else:
            raise DiscoveryError(errno.EINVAL,
                "Node health generator is already busy in processing previous request.")
        return status

    def get_gen_node_health_status(self):
        """Returns the below status on last node health generation request.

        "processing" if last health generation request is being processed.
        "success" if health generation request is completed.
        """
        # The marker file will be created at request processing start time.
        # Then it will be removed once request is completed. So that upcoming
        # request will be allowed.
        if os.path.exists(self.gen_marker):
            return self.PROCESSING
        else:
            return self.SUCCESSFUL

    def get_node_health(self, rpath:str=None, cached:bool=True):
        """Fetch and display node health for given rpath.

        rpath: Resource path in resource map to fetch its health.
            If rpath is not given, it will fetch whole Cortx Node
            data health and display.
            Examples:
            "no-cluster>site_001>rack_001>cortx_node_1>sm_001>hw>disks>disk_001"
            "no-cluster>site_001>rack_001>cortx_node_1>sm_001"
            "no-cluster>site_001>rack_001>cortx_node_1>rss_5u84_001>hw>psus"
        cached: Parse resource health map from cached file in FS.
            If not cached file found, then generate a new one for cache.
        """
        health_info = {}
        if rpath:
            health_info.update({"rpath": ""})
        if not cached:
            self.generate_node_health(rpath=rpath)

        # TODO: Look into Fs for reading cached data

        print(json.dumps(health_info))

    def show_resource_map(self, rpath:str=None):
        """Show list of resource types discovered.

        rpath: Resource path in resource map
            If rpath is given, parse resource map and collect
            sub nodes discovered.
        """
        pass
