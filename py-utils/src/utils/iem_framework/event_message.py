#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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

import json
import time
import errno
from cortx.template import Singleton
from cortx.utils.conf_store import Conf
from cortx.utils.iem_framework.error import EventMessageError
from cortx.utils.message_bus import MessageProducer, MessageConsumer


class EventMessage(metaclass=Singleton):
    """ Event Message framework to generate alerts """

    _conf_file = "json:///etc/cortx/cluster.conf"

    # VALID VALUES for IEC Components
    _SEVERITY_LEVELS = {
        'A': 'Alert',
        'X': 'Critical',
        'E': 'Error',
        'W': 'Warning',
        'N': 'Notice',
        'C': 'Configuration',
        'I': 'Informational',
        'D': 'Detail',
        'B': 'Debug'
    }
    _SOURCE = {
        'H': 'Hardware',
        'S': 'Software',
        'F': 'Firmware',
        'O': 'OS'
    }

    @classmethod
    def __init__(cls):
        try:
            Conf.load('cluster', cls._conf_file)
            ids = Conf.get('cluster', 'server_node')
            cls._site_id = int(ids['site_id'])
            cls._rack_id = int(ids['rack_id'])
            cls._node_id = int(ids['node_id'])
        except Exception as e:
            raise EventMessageError(errno.EINVAL, "Invalid config in %s. %s", \
                cls._conf_file, e)

    @classmethod
    def init(cls, component: str, source: str):
        """ Set the Event Message context """
        cls._component = component
        cls._source = source
        cls()

        if cls._component is None:
            raise EventMessageError(errno.EINVAL, "Invalid component type: %s", \
                cls._component)

        if cls._source not in cls._SOURCE.keys():
            raise EventMessageError(errno.EINVAL, "Invalid source type: %s", \
                cls._source)

        cls._producer = MessageProducer(producer_id='event_producer', \
            message_type='IEM', method='sync')

    @classmethod
    def send(cls, module: str, event_id: str, severity: str, message: str, \
        site_id: str = None, rack_id: str = None, node_id: str = None, \
        event_time: float = None, *params):
        """ Sends IEM alert message """

        site_id = site_id if site_id is not None else cls._site_id
        rack_id = rack_id if rack_id is not None else cls._rack_id
        node_id = node_id if node_id is not None else cls._node_id
        event_time = event_time if event_time is not None else time.time()

        # Validate attributes before sending
        for attribute in [module, event_id, message, site_id, node_id, rack_id]:
            if attribute is None:
                raise EventMessageError(errno.EINVAL, "Invalid IEM attributes \
                    %s", attribute)

        if severity not in cls._SEVERITY_LEVELS:
            raise EventMessageError(errno.EINVAL, "Invalid severity level: %s" \
                , severity)

        alert = json.dumps({
            'iem': {
                'version': '1',
                'info': {
                    'severity': cls._SEVERITY_LEVELS[severity],
                    'type': cls._SOURCE[cls._source],
                    'event_time': event_time
                    },
                'location': {
                    'site_id': cls._site_id,
                    'node_id': cls._node_id,
                    'rack_id': cls._rack_id
                    },
                'source': {
                    'site_id': site_id,
                    'node_id': node_id,
                    'rack_id': rack_id,
                    'component': cls._component,
                    'module': module
                    },
                'contents': {
                    'event': event_id,
                    'message': message,
                    'params': params,
                }
            }
        })

        cls._producer.send([alert])

    @classmethod
    def subscribe(cls, component: str, **filters):
        """ Subscribe to IEM alerts """
        if component is None:
            raise EventMessageError(errno.EINVAL, "Invalid component type: %s", \
               component)

        cls._consumer = MessageConsumer(consumer_id='event_consumer', \
            consumer_group=component, message_types=['IEM'], \
            auto_ack=True, offset='earliest')


    @classmethod
    def receive(cls):
        """ Receive IEM alert message """
        alert = cls._consumer.receive()
        if alert is not None:
            try:
                return json.loads(alert.decode('utf-8'))
            except Exception as e:
                raise EventMessageError(errno.EPERM, "Unable to load the json. \
                    %s", e)
        return alert