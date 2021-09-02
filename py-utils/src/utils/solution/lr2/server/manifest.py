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
# please email opensource@seagate.com or cortx-questions@seagate.com

import errno
import time

from cortx.utils.discovery.error import ResourceMapError
from service.software import Service
from server.server_resource_map import ServerResourceMap


class ServerManifest():
    """
    ServerManifest class provides resource map and related information
    like health.
    """

    name = "server_manifest"

    def __init__(self):
        """Initialize server manifest."""
        super().__init__()
        sw_resources = {
            'os': self.get_os_server_info,
            'cortx_sw_services': self.get_cortx_service_info,
            'external_sw_services': self.get_external_service_info
        }
        self.server_resources = {
            "sw": sw_resources
        }
        self.service = Service()
        self.HEALTH_UNDESIRED_VALS = ["NA", "N/A", ""]
        self.resource_indexing_map = {
            "sw": {
                "cortx_sw_services": "['uid']",
                "external_sw_services": "['uid']"
            }
        }

    def get_data(self, rpath):
        """Fetch manifest information for given rpath."""
        info = {}
        resource_found = False
        nodes = rpath.strip().split(">")
        leaf_node, _ = ServerResourceMap.get_node_info(nodes[-1])
        # Fetch manifest information for all sub nodes
        if leaf_node == "server":
            # Example rpath: 'node>server[0]'
            info = self.get_server_info()
            resource_found = True
        elif leaf_node == "sw":
            # Example rpath: 'node>server[0]>sw'
            for resource, method in self.server_resources[leaf_node].items():
                try:
                    info.update({resource: method()})
                    resource_found = True
                except Exception:
                    info = None
        else:
            for node in nodes:
                resource, _ = ServerResourceMap.get_node_info(node)
                for res_type in self.server_resources:
                    method = self.server_resources[res_type].get(resource)
                    if not method:
                        continue
                    try:
                        info = method()
                        resource_found = True
                    except Exception:
                        info = None
                if resource_found:
                    break

        if not resource_found:
            msg = f"Invalid rpath or manifest provider doesn't have support for'{rpath}'."
            raise ResourceMapError(errno.EINVAL, msg)

        info = ServerManifest.normalize_kv(info, self.HEALTH_UNDESIRED_VALS,
            "Not Available")
        return info

    def get_server_info(self):
        """Get server manifest information."""
        server = []
        info = {}
        for res_type in self.server_resources:
            info.update({res_type: {}})
            for fru, method in self.server_resources[res_type].items():
                try:
                    info[res_type].update({fru: method()})
                except Exception:
                    info[res_type].update({fru: []})
        info["last_updated"] = int(time.time())
        server.append(info)
        return server

    def get_cortx_service_info(self):
        """Get cortx service info in required format."""
        cortx_services = self.service.get_cortx_service_list()
        cortx_service_info = self.get_service_info(cortx_services)
        sort_key_path = self.resource_indexing_map["sw"]["cortx_sw_services"]
        cortx_service_info = ServerManifest.sort_by_specific_kv(
            cortx_service_info, sort_key_path)
        return cortx_service_info

    def get_external_service_info(self):
        """Get external service info in required format."""
        external_services = self.service.get_external_service_list()
        external_service_info = self.get_service_info(external_services)
        sort_key_path = self.resource_indexing_map["sw"]["external_sw_services"]
        external_service_info = ServerManifest.sort_by_specific_kv(
            external_service_info, sort_key_path)
        return external_service_info

    def get_service_info(self, services):
        """Returns node server services info."""
        services_info = []
        for service in services:
            response = self.service.get_systemd_service_info(service)
            if response is not None:
                uid, _, health_description, _, specifics = response
                service_info = {
                    "uid": uid,
                    "type": "software",
                    "description": health_description,
                    "product": specifics[0].pop("service_name"),
                    "manufacturer": "Not Applicable",
                    "serial_number": "Not Applicable",
                    "part_number": "Not Applicable",
                    "version": specifics[0].pop("version"),
                    "last_updated": int(time.time()),
                    "specifics": specifics
                }
                services_info.append(service_info)
        return services_info

    def get_os_server_info(self):
        """Returns node server os info."""
        os_data = []
        specifics = ServerManifest.get_os_info()
        if specifics:
            os_info = {
                "uid": specifics.get("id", "NA"),
                "type": "software",
                "description": "OS information",
                "product": specifics.get("pretty_name", "NA"),
                "manufacturer": specifics.get("manufacturer_name",
                                    "Not Applicable"),
                "serial_number": "Not Applicable",
                "part_number": "Not Applicable",
                "version": specifics.get("version", "NA"),
                "last_updated": int(time.time()),
                "specifics": [specifics]
            }
            os_data.append(os_info)
        return os_data

    @staticmethod
    def normalize_kv(item, input_v, replace_v):
        """Normalize all values coming from input as per requirement."""
        if isinstance(item, dict):
            return {key: ServerManifest.normalize_kv(value, input_v, replace_v)
                for key, value in item.items()}
        elif isinstance(item, list):
            return [ServerManifest.normalize_kv(_, input_v, replace_v) for _ in item]
        elif item in input_v if isinstance(input_v, list) else item == input_v:
            return replace_v
        else:
            return item

    @staticmethod
    def get_os_info():
        """Returns OS information from /etc/os-release."""
        os_release = ""
        os_info = {}
        with open("/etc/os-release") as f:
            os_release = f.read()
        if os_release:
            os_lst = os_release.split("\n")
            for line in os_lst:
                data = line.split('=')
                if len(data)>1 and data[1].strip() != "":
                    key = data[0].strip().lower().replace(" ","_")
                    value = data[1].strip().replace("\"","")
                    os_info.update({key: value})
        return os_info

    @staticmethod
    def sort_by_specific_kv(data, key_path):
        """
        Accept list of dictionary and sort by key value.
        data: list of dictionary
               Examples:
                    [{},{}]
        key_path: Sort list on the basis of the key path.
               Examples:
                    '["health"]["specifics"][0]["serial-number"]'
        """
        sorted_data = []
        try:
            if key_path and data:
                sorted_data = sorted(data, key=lambda k: eval(f'{k}{key_path}'))
            else:
                sorted_data = data
        except Exception:
            sorted_data = data
        return sorted_data
