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

import os

from cortx.utils.process import SimpleProcess
from cortx.utils.service.service_handler import DbusServiceHandler
from cortx.utils.errors import ServiceError
from dbus import PROPERTIES_IFACE, DBusException, Interface


class Service:
    """ Provides methods to fetch information for systemd services """

    name = "Service"

    def __init__(self):
        """Initialize the class."""
        self._bus, self._manager = DbusServiceHandler._get_systemd_interface()
        self.DEFAULT_RECOMMENDATION = 'Please Contact Seagate Support.'
        self.SYSTEMD_BUS = "org.freedesktop.systemd1"
        self.SERVICE_IFACE = "org.freedesktop.systemd1.Service"
        self.UNIT_IFACE = "org.freedesktop.systemd1.Unit"

    @staticmethod
    def get_external_service_list():
        """Get list of external services."""
        # TODO use solution supplied from RE for getting
        # list of external services.
        external_services = [
            "hare-consul-agent.service",
            "elasticsearch.service",
            "multipathd.service",
            "statsd.service",
            "rsyslog.service",
            "slapd.service",
            "lnet.service",
            "salt-master.service",
            "salt-minion.service",
            "glusterd.service",
            "scsi-network-relay.service",
            "kafka.service",
            "kafka-zookeeper.service"
        ]
        return external_services

    @staticmethod
    def get_cortx_service_list():
        """Get list of cortx services."""
        # TODO use solution supplied from HA for getting
        # list of cortx services or by parsing resource xml from PCS
        cortx_services = [
            "motr-free-space-monitor.service",
            "s3authserver.service",
            "s3backgroundproducer.service",
            "s3backgroundconsumer.service",
            "hare-hax.service",
            "haproxy.service",
            "sspl-ll.service",
            "kibana.service",
            "csm_agent.service",
            "csm_web.service",
            "event_analyzer.service",
        ]
        return cortx_services

    @staticmethod
    def get_service_info_from_rpm(service, prop):
        """
        Get specified service property from its corrosponding RPM.

        eg. (kafka.service,'LICENSE') -> 'Apache License, Version 2.0'
        """
        # TODO Include service execution path in systemd_path_list
        systemd_path_list = ["/usr/lib/systemd/system/",
                             "/etc/systemd/system/"]
        result = "NA"
        for path in systemd_path_list:
            # unit_file_path represents the path where
            # systemd service file resides
            # eg. kafka service -> /etc/systemd/system/kafka.service
            unit_file_path = path + service
            if os.path.isfile(unit_file_path):
                # this command will return the full name of RPM
                # which installs the service at given unit_file_path
                # eg. /etc/systemd/system/kafka.service -> kafka-2.13_2.7.0-el7.x86_64
                command = f"rpm -qf {unit_file_path}"
                service_rpm, _, ret_code = SimpleProcess(command).run()
                if ret_code != 0:
                    return result
                try:
                    service_rpm = service_rpm.decode("utf-8")
                except AttributeError:
                    return result
                # this command will extract specified property from given RPM
                # eg. (kafka-2.13_2.7.0-el7.x86_64, 'LICENSE') -> 'Apache License, Version 2.0'
                command = f"rpm -q --queryformat %{{prop}} {service_rpm}"
                result, _, ret_code = SimpleProcess(command).run()
                if ret_code != 0:
                    return result
                try:
                    # returned result should be in byte which need to be decoded
                    # eg. b'Apache License, Version 2.0' -> 'Apache License, Version 2.0'
                    result = result.decode("utf-8")
                except AttributeError:
                    return result
                break
        return result

    def get_systemd_service_info(self, service_name):
        """Get info of specified service using dbus API."""
        try:
            unit = self._bus.get_object(
                self.SYSTEMD_BUS, self._manager.LoadUnit(service_name))
            properties_iface = Interface(unit, dbus_interface=PROPERTIES_IFACE)
        except DBusException:
            return None
        path_array = properties_iface.Get(self.SERVICE_IFACE, 'ExecStart')
        try:
            command_line_path = str(path_array[0][0])
        except IndexError:
            command_line_path = "NA"

        is_installed = True if command_line_path != "NA" or 'invalid' in properties_iface.Get(
            self.UNIT_IFACE, 'UnitFileState') else False
        uid = str(properties_iface.Get(self.UNIT_IFACE, 'Id'))
        if not is_installed:
            health_status = "NA"
            health_description = f"Software enabling {uid} is not installed"
            recommendation = "NA"
            specifics = [
                {
                    "service_name": uid,
                    "description": "NA",
                    "installed": str(is_installed).lower(),
                    "pid": "NA",
                    "state": "NA",
                    "substate": "NA",
                    "status": "NA",
                    "license": "NA",
                    "version": "NA",
                    "command_line_path": "NA"
                }
            ]
        else:
            service_license = "NA"
            version = "NA"
            service_description = str(
                properties_iface.Get(self.UNIT_IFACE, 'Description'))
            state = str(properties_iface.Get(self.UNIT_IFACE, 'ActiveState'))
            substate = str(properties_iface.Get(self.UNIT_IFACE, 'SubState'))
            service_status = 'enabled' if 'disabled' not in properties_iface.Get(
                self.UNIT_IFACE, 'UnitFileState') else 'disabled'
            pid = "NA" if state == "inactive" else str(
                properties_iface.Get(self.SERVICE_IFACE, 'ExecMainPID'))
            try:
                version = self.get_service_info_from_rpm(
                    uid, "VERSION")
            except ServiceError:
                version = "NA"
            try:
                service_license = self.get_service_info_from_rpm(
                    uid, "LICENSE")
            except ServiceError:
                service_license = "NA"

            specifics = [
                {
                    "service_name": uid,
                    "description": service_description,
                    "installed": str(is_installed).lower(),
                    "pid": pid,
                    "state": state,
                    "substate": substate,
                    "status": service_status,
                    "license": service_license,
                    "version": version,
                    "command_line_path": command_line_path
                }
            ]
            if state == 'active' and substate == 'running':
                health_status = 'OK'
                health_description = f"{uid} is in good health"
                recommendation = "NA"
            else:
                health_status = state
                health_description = f"{uid} is not in good health"
                recommendation = self.DEFAULT_RECOMMENDATION

        return uid, health_status, health_description, recommendation, specifics
