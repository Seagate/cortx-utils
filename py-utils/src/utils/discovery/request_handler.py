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

import os
import re
import time
import errno
import psutil
from datetime import datetime

from cortx.utils import const
from cortx.utils.conf_store import MappedConf
from cortx.utils.kv_store import KvStoreFactory
from cortx.utils.discovery.error import DiscoveryError
from cortx.utils.discovery.resource import Resource, ResourceFactory

# Load cortx common config
store_type = "json"
cluster_conf = MappedConf(const.CLUSTER_CONF)
local_storage_path = cluster_conf.get('cortx>common>storage>local')
config_url = "%s://%s" % (store_type, os.path.join(local_storage_path, 'utils/conf/cortx.conf'))
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


class RequestHandler:

    """This handles resource map generation requests."""

    ROOT_NODE = "node"
    INPROGRESS = "In-progress"
    SUCCESS = "Success"
    FAILED = "Failed"

    @staticmethod
    def _get_node_details(node):
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
    def _add_discovery_request(rpath, req_id, url):
        """Updates new request information."""
        req_info = {
            "rpath": rpath,
            "status": RequestHandler.INPROGRESS,
            "url": url,
            "time": datetime.strftime(
                datetime.now(), '%Y-%m-%d %H:%M:%S')
        }
        req_register.set(["%s" % req_id], [req_info])

    @staticmethod
    def _set_discovery_request_processed(req_id, status):
        """Updates processed request information."""
        req_info = req_register.get(["%s" % req_id])[0]
        req_info.update({
            "status": status,
             "time": datetime.strftime(
                datetime.now(), '%Y-%m-%d %H:%M:%S')
        })
        req_register.set(["%s" % req_id], [req_info])

    @staticmethod
    def _update_resource_map(rpath, request_type):
        """
        Fetch information based on request type and update.

        resource map for given rpath.
        """
        # Parse rpath and find left node
        nodes = rpath.strip().split(">")
        leaf_node, _ = RequestHandler._get_node_details(nodes[-1])

        for num, node in enumerate(nodes, 1):
            node, _ = RequestHandler._get_node_details(node)
            resource = ResourceFactory.get_instance(node, rpath)

            # Validate next node is its child
            child_found = False
            if node != leaf_node:
                next_node, _ = RequestHandler._get_node_details(
                    nodes[num])
                child_found = resource.has_child(next_node)
                if resource.childs and not child_found:
                    raise DiscoveryError(
                        errno.EINVAL, "Invalid rpath '%s'" % rpath)

            # Fetch resource information and update store file
            if node == leaf_node and len(resource.childs) != 0:
                for child in resource.childs:
                    child_inst = ResourceFactory.get_instance(child, rpath)
                    main = resource(child_resource=child_inst)
                    joined_rpath = rpath + ">" + child
                    main.set(joined_rpath,
                             main.get_data(joined_rpath, request_type))
                break
            elif node == leaf_node or len(resource.childs) == 0:
                main = resource(child_resource=None)
                main.set(rpath, main.get_data(rpath, request_type))
                break

    @staticmethod
    def process(rpath: str, req_id: str, store_url: str, req_type: str = "health"):
        """
        Creates resource map and updates resource information for given.

        request type.

        rpath: Resource path for information fetched
        req_id: Request ID to be processed and used in store url format
        store_url: Location to update resource information
        req_type: Request type, i.e 'health' or 'manifest' or ...
        """
        if not store_url and not rpath:
            # Create static store url
            rpath = RequestHandler.ROOT_NODE
            store_type = common_config.get(["discovery>resource_map>store_type"])[0]
            resource_map_loc = common_config.get(["discovery>resource_map>location"])[0]
            data_file_map = {
                "health": "node_health_info.%s" % (store_type),
                "manifest": "node_manifest_info.%s" % (store_type)
                }
            data_file = os.path.join(resource_map_loc,
                                     data_file_map[req_type])
            store_url = "%s://%s" % (store_type, data_file)

        elif not store_url and rpath:
            # Create request_id based store_url
            store_type = common_config.get(["discovery>resource_map>store_type"])[0]
            resource_map_loc = common_config.get(["discovery>resource_map>location"])[0]
            data_file_map = {
                "health": "node_health_info_%s.%s" % (
                    req_id, store_type),
                "manifest": "node_manifest_info_%s.%s" % (
                    req_id, store_type)
                }
            data_file = os.path.join(resource_map_loc,
                                     data_file_map[req_type])
            store_url = "%s://%s" % (store_type, data_file)

        else:
            # Use given store url
            rpath = rpath if rpath else RequestHandler.ROOT_NODE

        try:
            # Initialize resource map
            Resource.init(store_url)
            # Process request
            RequestHandler._add_discovery_request(rpath, req_id, store_url)
            RequestHandler._update_resource_map(rpath, req_type)
            RequestHandler._set_discovery_request_processed(
                req_id,RequestHandler.SUCCESS)
        except Exception as err:
            status = RequestHandler.FAILED + f" - {err}"
            RequestHandler._set_discovery_request_processed(
                req_id, status)

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
            system_time = time.strptime(
                req_register.get(["%s>time" % req_id])[0],
                '%Y-%m-%d %H:%M:%S')
            req_start_time = int(time.mktime(system_time))
            current_time = int(time.time())
            is_req_expired = (current_time - req_start_time) > expiry_sec
            if is_req_expired or (last_reboot > req_start_time and\
                status is RequestHandler.INPROGRESS):
                # Set request state as failed
                RequestHandler._set_discovery_request_processed(
                    req_id, "Failed - request is expired.")
            status = req_register.get(["%s>status" % req_id])[0]

        return status

    @staticmethod
    def get_resource_map_location(req_id, req_type):
        """Returns backend store URL."""
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
            data_file_map = {
                "health": "node_health_info.%s" % (store_type),
                "manifest": "node_manifest_info.%s" % (store_type)
                }
            data_file = os.path.join(
                resource_map_loc, data_file_map[req_type])
            if not os.path.exists(data_file):
                raise DiscoveryError(
                    errno.ENOENT,
                    "%s resource map is unavailable. "\
                        "Please generate." % req_type.title())

            store_url = "%s://%s" % (store_type, data_file)

        return store_url
