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

import importlib.util
import inspect
import os
import sys

from cortx.utils.conf_store import Conf


script_path = os.path.realpath(__file__)
data_file = os.path.join(os.path.dirname(script_path), "dm_config.ini")
dm_config = "dm_config"
Conf.load(dm_config, "ini://%s" % data_file)


def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Resource:

    def __init__(self, name, child_resource=None, inst="*"):
        self._name = name
        self._instance = inst
        self._child_resource = child_resource
        self.health_provider_map = {
            "storage": "storage",
            "compute": "server"
            }

    @property
    def name(self):
        return self._name

    @property
    def child_resource(self):
        return self._child_resource

    @property
    def instance(self):
        return self._instance

    def get_health_provider_module(self):
        """Look for dm package in health provider path"""
        provider = Conf.get(
            dm_config, "HEALTH_PROVIDER>%s" % self.health_provider_map[self.name])
        if provider == "dm":
            provider_loc = os.path.dirname(os.path.realpath(__file__)) + "/dm/"
        else:
            provider_loc = "/opt/seagate/cortx/%s/dm/" % provider
        sys.path.append(os.path.dirname(provider_loc))
        return __import__(self.health_provider_map[self.name])

    def get_health_info(self, rid):
        """
        rid:
            "hw>controllers"
            "hw>controllers[0]"
            "hw>controllers[0]>health"
            "hw>controllers[0]>health>status"
            "fw>disk_groups"
        """
        info = None
        module = self.get_health_provider_module()
        members = inspect.getmembers(module, inspect.isclass)
        for _, cls in members:
            if hasattr(cls, 'name') and self.health_provider_map[self.name] == cls.name:
                info = cls().get_health_info(rid)
                break
        return info


class Server(Resource):

    name = "compute"
    childs = []

    def __init__(self, child_resource, inst="*"):
        super().__init__(self.name, child_resource, inst)

    @staticmethod
    def has_child(resource):
        return resource in Nodes.childs


class Storage(Resource):

    name = "storage"
    childs = []

    def __init__(self, child_resource, inst="*"):
        super().__init__(self.name, child_resource, inst)

    @staticmethod
    def has_child(resource):
        return resource in Nodes.childs


class Nodes(Resource):

    name = "nodes"
    childs = ["compute", "storage"]

    def __init__(self, child_resource, inst="*"):
        super().__init__(child_resource, inst)

    @staticmethod
    def has_child(resource):
        return resource in Nodes.childs
