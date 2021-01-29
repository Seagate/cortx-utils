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

import dbus
import inspect
import errno
import sys


class ServiceError(Exception):
    """ Generic Exception with error code and output """
    _module = 'service'

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "%s: error(%d): %s" %(self._module, self._rc, self._desc)


class ServiceHandler:
    """ Handler for Service Control """

    @staticmethod
    def get(handler_type: str):
        members = inspect.getmembers(sys.modules[__name__])
        for name, cls in members:
            if name != "Handler" and name.endswith("Handler"):
                if cls.name == handler_type:
                    return cls
        raise ServiceError(errno.EINVAL, "Invalid handler type %s" %handler_type)

    def process(self, action, service_name):
        pass


class DbusServiceHandler:
    """ Handler for Service Control using DBUS interface """
    name = "dbus"

    def process(self, action: str, service_name: str):
        if action not in ['enable', 'disable', 'start', 'stop', 'restart']:
            raise ServiceError(errno.EINVAL, "Invalid action '%s' for the service %s" \
                %(action, service_name))
        try:
            system_bus = dbus.SystemBus()
            systemd1 = system_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
            dbus_manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
            if action == 'disable':
                dbus_manager.DisableUnitFiles([f'{service_name}'], False)
                dbus_manager.Reload()
            elif action == 'enable':
                dbus_manager.EnableUnitFiles([f'{service_name}'], False, True)
                dbus_manager.Reload()
            elif action == 'start':
                dbus_manager.StartUnit(f'{service_name}', 'fail')
            elif action == 'stop':
                dbus_manager.StopUnit(f'{service_name}', 'fail')
            elif action == 'restart':
                dbus_manager.RestartUnit(f'{service_name}', 'fail')

        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL, "Failed to '%s' on '%s' due to error. %s" \
                %(action, service_name, err))


class Service:
    """ Represents a Service which needs to be controlled """

    def __init__(self, handler_type: str):
        self._handler = ServiceHandler.get(handler_type)

    def process(self, action: str, *args):
        self._handler.process(self, action, *args)
