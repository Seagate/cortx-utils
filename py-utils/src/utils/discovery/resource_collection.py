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

from cortx.utils.discovery.resource import Resource


class Server(Resource):

    name = "server"
    childs = []

    def __init__(self, child_resource=None):
        super().__init__(self.name, child_resource)

    @staticmethod
    def has_child(child_resource):
        return child_resource in Server.childs


class Storage(Resource):

    name = "storage"
    childs = []

    def __init__(self, child_resource=None):
        super().__init__(self.name, child_resource)

    @staticmethod
    def has_child(child_resource):
        return child_resource in Storage.childs


class Node(Resource):

    name = "node"
    childs = ["server", "storage"]

    def __init__(self, child_resource=None):
        super().__init__(self.name, child_resource)
        self.child = child_resource()

    @staticmethod
    def has_child(child_resource):
        return child_resource in Node.childs

    def get_data(self, rpath, request_type):
        return self.child.get_data(rpath, request_type)
