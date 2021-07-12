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
from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.discovery.resource import Resource, ResourceFactory
from cortx.utils.kv_store import KvStoreFactory

# Load cortx common config
store_type = "json"
config_url = "%s://%s" % (store_type, const.CORTX_CONF_FILE)
common_config = KvStoreFactory.get_instance(config_url)
common_config.load()

# Load Discovery request status tracker
try:
    os.makedirs(common_config.get(
        ["discovery>resource_map>location"])[0], exist_ok=True)
except PermissionError as err:
    raise DiscoveryError(
        errno.EACCES,
        "Failed to create default store directory. %s" % err)
requests_url = "%s://%s" % (store_type, os.path.join(
    common_config.get(["discovery>resource_map>location"])[0],
    "requests.json"))
req_register = KvStoreFactory.get_instance(requests_url)
req_register.load()


class NodeHealth:
    """This generates node health information and updates map"""

    ROOT_NODE = "node"
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
    def add_discovery_request(rpath, req_id, url):
        """Updates new request information"""
        req_register.set(["%s>rpath" % req_id], [rpath])
        req_register.set(["%s>status" % req_id], [NodeHealth.INPROGRESS])
        req_register.set(["%s>url" % req_id], [url])
        req_register.set(["%s>time" % req_id], [int(time.time())])

    @staticmethod
    def set_discovery_request_processed(req_id, status):
        """Updates processed request information"""
        req_register.set(["%s>status" % req_id], [status])
        req_register.set(["%s>time" % req_id], [int(time.time())])

    @staticmethod
    def update_resource_map(rpath, manifest):
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
                    if manifest:
                        main.set(joined_rpath, main.get_manifest_info(joined_rpath))
                    else:
                        main.set(joined_rpath, main.get_health_info(joined_rpath))
                break
            elif node == leaf_node or len(resource.childs) == 0:
                main = resource(child_resource=None)
                if manifest:
                    main.set(rpath, main.get_manifest_info(rpath))
                else:
                    main.set(rpath, main.get_health_info(rpath))
                break

    @staticmethod
    def generate(rpath: str, req_id: str, store_url: str, manifest: bool = False):
        """Generates node health information and updates resource map"""
        if not store_url and not rpath:
            # Create static store url
            rpath = NodeHealth.ROOT_NODE
            store_type = common_config.get(["discovery>resource_map>store_type"])[0]
            resource_map_loc = common_config.get(["discovery>resource_map>location"])[0]
            data_file = os.path.join(resource_map_loc,
                "node_health_info.%s" % (store_type))
            if manifest:
                data_file = os.path.join(resource_map_loc,
                    "manifest_info.%s" % (store_type))
            store_url = "%s://%s" % (store_type, data_file)

        elif not store_url and rpath:
            # Create request_id based store_url
            store_type = common_config.get(["discovery>resource_map>store_type"])[0]
            resource_map_loc = common_config.get(["discovery>resource_map>location"])[0]
            data_file = os.path.join(resource_map_loc,
                "node_health_info_%s.%s" % (req_id, store_type))
            if manifest:
                data_file = os.path.join(resource_map_loc,
                    "manifest_%s.%s" % (req_id, store_type))
            store_url = "%s://%s" % (store_type, data_file)

        else:
            # Use given store url
            rpath = rpath if rpath else NodeHealth.ROOT_NODE

        try:
            # Initialize resource map
            Resource.init(store_url)
            # Process request
            NodeHealth.add_discovery_request(rpath, req_id, store_url)
            NodeHealth.update_resource_map(rpath, manifest)
            NodeHealth.set_discovery_request_processed(req_id, NodeHealth.SUCCESS)
        except Exception as err:
            status = NodeHealth.FAILED + f" - {err}"
            NodeHealth.set_discovery_request_processed(req_id, status)

    @staticmethod
    def get_processing_status(req_id):
        """
        Returns "in-progress" if any request is being processed.
        Otherwise returns "Success" or "Failed (with reason)" status.
        """
        status_list = req_register.get(["%s>status" % req_id])
        status = status_list[0] if status_list else None

        if not status:
            raise DiscoveryError(
                errno.EINVAL, "Request ID '%s' not found." % req_id)
        else:
            # Set failed status to stale request ID
            expiry_sec = int(common_config.get(["discovery>resource_map>expiry_sec"])[0])
            last_reboot = int(psutil.boot_time())
            # Set request is expired if processing time exceeds
            req_start_time = int(req_register.get(["%s>time" % req_id])[0])
            current_time = int(time.time())
            is_req_expired = (current_time - req_start_time) > expiry_sec
            if (last_reboot > req_start_time or is_req_expired) and \
                status is NodeHealth.INPROGRESS:
                # Set request state as failed
                NodeHealth.set_discovery_request_processed(
                    req_id, "Failed - request is expired.")
            status = req_register.get(["%s>status" % req_id])[0]

        return status

    @staticmethod
    def get_resource_map_location(req_id):
        """Returns backend store URL"""
        if req_id:
            url_list = req_register.get(["%s>url" % req_id])
            store_url = url_list[0] if url_list else None
            if not store_url:
                raise DiscoveryError(
                    errno.EINVAL, "Request ID '%s' not found." % req_id)
        else:
            # Look for static data or cached file
            store_type = common_config.get(["discovery>resource_map>store_type"])[0]
            resource_map_loc = common_config.get(["discovery>resource_map>location"])[0]
            data_file = os.path.join(resource_map_loc,
                "node_health_info.%s" % (store_type))

            if not os.path.exists(data_file):
                raise DiscoveryError(
                    errno.ENOENT,
                    "Resource health map is unavailable. Please generate.")

            store_url = "%s://%s" % (store_type, data_file)

        return store_url
