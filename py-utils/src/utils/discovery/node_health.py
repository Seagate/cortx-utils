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
import json
import os
import psutil
import re
import time

from cortx.utils import const
from cortx.utils.conf_store import Conf
from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.discovery.resource import Resource, ResourceFactory

# Setup DM request status tracker
os.makedirs(const.DM_CONFIG_PATH, exist_ok=True)
os.makedirs(const.DM_RESOURCE_MAP_PATH, exist_ok=True)
store_type = "json"
dm_requests = "dm_requests"
dm_requests_file = os.path.join(
    const.DM_CONFIG_PATH, "%s.%s" % (dm_requests, store_type))
dm_requests_url = "%s://%s" % (store_type, dm_requests_file)
if not os.path.exists(dm_requests_file):
    with open(dm_requests_file, "w+") as f:
        json.dump({}, f, indent=2)
Conf.load(dm_requests, dm_requests_url)


class NodeHealth:
    """This generates node health information and updates map"""

    INPROGRESS = "In-progress"
    SUCCESS = "Success"
    FAILED = "Failed"

    @staticmethod
    def get_node_details(node):
        """
        Parse node information and returns left string and instance.
        Example
            "storage"    -> ("storage", "*")
            "storage[0]" -> ("storage", "0")
        """
        res = re.search(r"(\w+)\[([\d]+)\]|(\w+)", node)
        inst = res.groups()[1] if res.groups()[1] else "*"
        node = res.groups()[0] if res.groups()[1] else res.groups()[2]
        return node, inst

    @staticmethod
    def add_dm_request(rpath, req_id, url):
        """Updates new request information"""
        Conf.set(dm_requests, "%s>rpath" % req_id, rpath)
        Conf.set(dm_requests, "%s>status" % req_id, NodeHealth.INPROGRESS)
        Conf.set(dm_requests, "%s>url" % req_id, url)
        Conf.set(dm_requests, "%s>time" % req_id, int(time.time()))
        Conf.save(dm_requests)

    @staticmethod
    def set_dm_request_processed(req_id, status):
        """Updates processed request information"""
        Conf.set(dm_requests, "%s>status" % req_id, status)
        Conf.set(dm_requests, "%s>time" % req_id, int(time.time()))
        Conf.save(dm_requests)

    @staticmethod
    def update_resource_map(rpath):
        """Update resource map for resources in rpath"""
        # Parse rpath and find left node
        nodes = rpath.strip().split(">")
        leaf_node, _ = NodeHealth.get_node_details(nodes[-1])

        for num, node in enumerate(nodes, 1):
            node, _ = NodeHealth.get_node_details(node)
            resource = ResourceFactory.get_instance(node, rpath)

            # Validate next node is its child
            child_found = False
            if node != leaf_node:
                next_node, _ = NodeHealth.get_node_details(nodes[num])
                child_found = resource.has_child(next_node)
                if resource.childs and not child_found:
                    raise DiscoveryError(
                        errno.EINVAL, "Invalid rpath '%s'" % rpath)

            # Fetch node health information
            if node == leaf_node and len(resource.childs) != 0:
                for child in resource.childs:
                    child_inst = ResourceFactory.get_instance(child, rpath)
                    main = resource(child_resource=child_inst)
                    joined_rpath = rpath + ">" + child
                    main.set(joined_rpath, main.get_health_info(joined_rpath))
                break
            elif node == leaf_node or len(resource.childs) == 0:
                main = resource(child_resource=None)
                main.set(rpath, main.get_health_info(rpath))
                break

    @staticmethod
    def generate(rpath: str, req_id: str):
        """Generates node health information and updates resource map"""
        try:
            # Initialize resource map
            data_file = os.path.join(const.DM_RESOURCE_MAP_PATH,
                "node_health_info_%s.%s" % (req_id, store_type))
            url = "%s://%s" % (store_type, data_file)
            Resource.init(url)
            # Process request
            NodeHealth.add_dm_request(rpath, req_id, url)
            NodeHealth.update_resource_map(rpath)
            NodeHealth.set_dm_request_processed(req_id, NodeHealth.SUCCESS)
        except Exception as err:
            status = NodeHealth.FAILED + f" - {err}"
            NodeHealth.set_dm_request_processed(req_id, status)

    @staticmethod
    def get_processing_status(req_id):
        """
        Returns "in-progress" if any request is being processed.
        Otherwise Node Health scan status is "Ready" or "Success".
        """
        status = Conf.get(dm_requests, "%s>status" % req_id)
        if not status:
            raise DiscoveryError(
                errno.EINVAL, "Request ID '%s' not found." % req_id)
        else:
            # Set failed status to stale request ID
            last_reboot = int(psutil.boot_time())
            req_start_time = int(Conf.get(dm_requests, "%s>time" % req_id))
            if (last_reboot > req_start_time) and status is NodeHealth.INPROGRESS:
                NodeHealth.set_dm_request_processed(
                    req_id, "Failed - request is expired.")
            status = Conf.get(dm_requests, "%s>status" % req_id)
        return status

    @staticmethod
    def get_resource_map_location(req_id):
        """Returns backend URL"""
        url = Conf.get(dm_requests, "%s>url" % req_id)
        if not url:
            raise DiscoveryError(
                errno.EINVAL, "Request ID '%s' not found." % req_id)
        return url
