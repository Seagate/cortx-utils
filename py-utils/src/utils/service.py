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

class Service:
    def __init__(self, service, action):
        self._service = service
        self._action = action
        system_bus = dbus.SystemBus()
        systemd1 = system_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        self.dbus_manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

    def run(self):
        pass

class EnableDisableService(Service):
    """Enable/Disable systemd services."""
    def __init__(self, service, action):
        super(EnableDisableService, self).__init__(service, action)

    def run(self, **args):
        """This will execute the action"""
        for key, value in args.items():
            setattr(self, key, value)

        try:
            if self._action == 'disable':
                self.dbus_manager.DisableUnitFiles([f'{self._service}'], False)
            else:
                self.dbus_manager.EnableUnitFiles([f'{self._service}'], False, True)
            self.dbus_manager.Reload()
            return
        
        except dbus.DBusException as err:
            print(f"Failed to {self._action} on {self._service} due to error : {err}")
            return 1


class SystemctlServiceAction(Service):
    """Start/Stop/Restart systemctl services."""
    def __init__(self, service, action):
        super(SystemctlServiceAction, self).__init__(service, action)

    def run(self, **args):
        """This will execute the action"""
        for key, value in args.items():
            setattr(self, key, value)

        try:
            if self._action == 'start':
                self.dbus_manager.StartUnit(f'{self._service}', 'fail')
            elif self._action == 'stop':
                self.dbus_manager.StopUnit(f'{self._service}', 'fail')
            elif self._action == 'restart':
                self.dbus_manager.RestartUnit(f'{self._service}', 'fail')
            else:
                print(f"Invalid action: f'{self._service}' :Please provide an appropriate action name for the service.")
                return 1
            return

        except dbus.DBusException as err:
            print(f"Failed to {self._action} on {self._service} due to error : {err}")
            return 1
