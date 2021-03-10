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

class DbusServiceHandler(ServiceHandler):
    """ Handler for Service Control using DBUS interface """
    name = "dbus"

    def __init__(self):
        self._system_bus, self._dbus_manager = \
            DbusServiceHandler._get_systemd_interface()

    @classmethod
    def _get_systemd_interface(cls):
        system_bus = dbus.SystemBus()
        systemd1 = system_bus.get_object('org.freedesktop.systemd1',
            '/org/freedesktop/systemd1')
        dbus_manager = dbus.Interface(systemd1,
            'org.freedesktop.systemd1.Manager')
        return system_bus, dbus_manager

    def start(self, service_name: str):
        """Starts systemd service using dbus interface."""
        try:
            self._dbus_manager.StartUnit(f'{service_name}', 'fail')
        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL,
                "Failed to start %s due to error. %s" %(service_name, err))

    def stop(self, service_name: str):
        """Stop systemd service using dbus interface."""
        try:
            self._dbus_manager.StopUnit(f'{service_name}', 'fail')
        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL,
                "Failed to stop %s due to error. %s" %(service_name, err))

    def restart(self, service_name: str):
        """Restart systemd service using dbus interface."""
        try:
            self._dbus_manager.RestartUnit(f'{service_name}', 'fail')
        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL,
                "Failed to restart %s due to error. %s" %(service_name, err))

    def enable(self, service_name: str):
        """Enable systemd service using dbus interface."""
        try:
            self._dbus_manager.EnableUnitFiles([f'{service_name}'], False, True)
            self._dbus_manager.Reload()
        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL,
                "Failed to enable %s due to error. %s" %(service_name, err))

    def disable(self, service_name: str):
        """Disable systemd service using dbus interface."""
        try:
            self._dbus_manager.DisableUnitFiles([f'{service_name}'], False)
            self._dbus_manager.Reload()
        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL,
                "Failed to disable %s due to error. %s" %(service_name, err))

    def get_state(self, service_name):
        """Returns ServiceState of the Service."""
        unit = self._system_bus.get_object('org.freedesktop.systemd1',
            self._dbus_manager.LoadUnit(service_name))
        Iunit = dbus.Interface(unit,
            dbus_interface='org.freedesktop.DBus.Properties')
        pid = str(Iunit.Get('org.freedesktop.systemd1.Service', 'ExecMainPID'))
        state = str(Iunit.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))
        substate = str(Iunit.Get('org.freedesktop.systemd1.Unit', 'SubState'))
        command_line =  list(Iunit.Get('org.freedesktop.systemd1.Service',
            'ExecStart'))
        service_state = ServiceState(pid, state, substate, command_line)
        return service_state

    def is_enabled(self, service_name):
        """Returns service status: enable/disable."""
        try:
            status = str(self._dbus_manager.GetUnitFileState(service_name))
            return status
        except dbus.DBusException as err:
            raise ServiceError(errno.EINVAL,
                "Can not check service status: enable/disable for %s, "
                "due to error: %s." % (service_name, err))

    def __cleanup__(self):
        del self._dbus_manager
        del self._system_bus

class ServiceState:
    """ Return service information:state, substate, pid, command_line_path. """

    def __init__(self, pid, state, substate, command_line_path):
        self._pid = pid
        self._state = state
        self._substate = substate
        self._command_line_path = command_line_path

    @property
    def pid(self):
        return self._pid

    @property
    def state(self):
        return self._state

    @property
    def substate(self):
        return self._substate

    @property
    def command_line_path(self):
        return self._command_line_path

class Service:
    """ Represents a Service which needs to be controlled """

    def __init__(self, service_name: str, handler_type: str=None):
        self._service_name = service_name
        if handler_type is None:
            handler_type = "dbus"
        self._handler = ServiceHandler.get(handler_type)

    def start(self):
        self._handler.start(self, self._service_name)

    def stop(self):
        self._handler.stop(self, self._service_name)

    def restart(self):
        self._handler.restart(self, self._service_name)

    def enable(self):
        self._handler.enable(self, self._service_name)

    def disable(self):
        self._handler.disable(self, self._service_name)

    def get_state(self):
        service_state = self._handler.get_state(self, self._service_name)
        return service_state

    def is_enabled(self):
        status = self._handler.is_enabled(self, self._service_name)
        return status
