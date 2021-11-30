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

import os
import json
import time
import errno
from cortx.utils.common import CortxConf
from cortx.utils import errors
from cortx.template import Singleton
from cortx.utils.conf_store import Conf
from cortx.utils.iem_framework.error import EventMessageError
from cortx.utils.message_bus import MessageProducer, MessageConsumer
from cortx.utils.log import Log


class EventMessage(metaclass=Singleton):
    """ Event Message framework to generate alerts """
    _producer = None
    _consumer = None

    # VALID VALUES for IEC Components
    _SEVERITY_LEVELS = {
        'A': 'alert',
        'X': 'critical',
        'E': 'error',
        'W': 'warning',
        'N': 'notice',
        'C': 'configuration',
        'I': 'informational',
        'D': 'detail',
        'B': 'debug'
    }
    _SOURCE = {
        'H': 'Hardware',
        'S': 'Software',
        'F': 'Firmware',
        'O': 'OS'
    }

    @staticmethod
    def _initiate_logger():
        """Initialize logger if required."""
        Conf.load('config_file', 'json:///etc/cortx/cortx.conf',
            skip_reload=True)
        # if Log.logger is already initialized by some parent process
        # the same file will be used to log all the messagebus related
        # logs, else standard iem.log will be used.
        if not Log.logger:
            LOG_DIR='/var/log'
            iem_log_dir = os.path.join(LOG_DIR, 'cortx/utils/iem')
            log_level = Conf.get('config_file', 'utils>log_level', 'INFO')
            Log.init('iem', iem_log_dir, level=log_level, \
                backup_count=5, file_size_in_mb=5)

    @classmethod
    def init(cls, component: str, source: str,\
        cluster_conf: str = 'yaml:///etc/cortx/cluster.conf'):
        """
        Set the Event Message context

        Parameters:
        component       Component that generates the IEM. For e.g. 'S3', 'SSPL'
        source          Single character that indicates the type of component.
                        For e.g. H-Hardware, S-Software, F-Firmware, O-OS
        cluster_conf    ConfStore URL of cluster.conf file
        """
        utils_index = 'utils_ind'
        CortxConf.init(cluster_conf=cluster_conf)
        local_storage = CortxConf.get_storage_path('local')
        utils_conf = os.path.join(local_storage, 'utils/conf/utils.conf')
        cls._conf_file = f'json://{utils_conf}'

        cls._component = component
        cls._source = source

        cls._initiate_logger()

        try:
            Conf.load(utils_index, cls._conf_file, skip_reload=True)
            machine_id = Conf.machine_id
            ids = Conf.get(utils_index, f'node>{machine_id}')
            cls._site_id = ids['site_id']
            cls._rack_id = ids['rack_id']
            cls._node_id = machine_id
            cls._cluster_id = ids['cluster_id']
        except Exception as e:
            Log.error("Invalid config in %s." % cls._conf_file)
            raise EventMessageError(errno.EINVAL, "Invalid config in %s. %s", \
                cls._conf_file, e)

        if cls._component is None:
            Log.error("Invalid component type: %s" % cls._component )
            raise EventMessageError(errno.EINVAL, "Invalid component type: %s", \
                cls._component)

        if cls._source not in cls._SOURCE.keys():
            Log.error("Invalid source type: %s" % cls._source)
            raise EventMessageError(errno.EINVAL, "Invalid source type: %s", \
                cls._source)

        cls._producer = MessageProducer(producer_id='event_producer', \
            message_type='IEM', method='sync', cluster_conf=cluster_conf)
        Log.info("IEM Producer initialized for component %s and source %s" % \
             (cls._component, cls._source))

    @classmethod
    def send(cls, module: str, event_id: str, severity: str, message_blob: str,\
        problem_cluster_id: str = None, problem_site_id: int = None, \
        problem_rack_id: int = None, problem_node_id: int = None, \
        problem_host: str = None, event_time: float = None):
        """
        Sends IEM alert message

        Parameters:
        module              Indicates the sub module of a component that
                            generated the IEM. i.e SSPL submodule like HPI.
        event_id            A numerical value that uniquely identifies an event.
        severity            The degree of impact an event has on the operation
                            of a component.
        message_blob        Blob alert message.
        problem_cluster_id  A alpha numerical value that indicates cluster ID.
                            (Problem Location)
        problem_site_id     Uniquely identifies a single data center site.
                            (Problem Location)
        problem_rack_id     A numerical value that identifies a single Rack in a
                            single site. (Problem Location)
        problem_node_id     A numerical value that indicates node ID. (UUID)
                            (Problem Location)
        problem_host        A string that indicates the hostname.
                            (Problem Location)
        event_time          Time of the event
        """

        import socket
        sender_host = socket.gethostname()

        cls._initiate_logger()
        if cls._producer is None:
            Log.error("IEM Producer not initialized.")
            raise EventMessageError(errors.ERR_SERVICE_NOT_INITIALIZED, \
                "Producer is not initialised")

        site_id = problem_site_id if problem_site_id is not None else \
            cls._site_id
        rack_id = problem_rack_id if problem_rack_id is not None else \
            cls._rack_id
        node_id = problem_node_id if problem_node_id is not None else \
            cls._node_id
        cluster_id = problem_cluster_id if problem_cluster_id is not None else \
            cls._cluster_id
        host = problem_host if problem_host is not None else sender_host

        event_time = event_time if event_time is not None else time.time()
        Log.debug("site_id: %s, rack_id: %s, node_id: %s, cluster_id: %s,\
             host: %s" % (site_id, rack_id, node_id, cluster_id, host))

        # Validate attributes before sending
        for attribute in [module, event_id, message_blob, site_id, rack_id, \
            node_id, cluster_id]:
            if attribute is None:
                Log.error("Invalid IEM attributes %s.", attribute)
                raise EventMessageError(errno.EINVAL, "Invalid IEM attributes \
                    %s", attribute)

        if severity not in cls._SEVERITY_LEVELS:
            Log.error("Invalid severity level: %s." % severity)
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
                    'cluster_id': cluster_id,
                    'site_id': site_id,
                    'rack_id': rack_id,
                    'node_id': node_id,
                    'host': host
                    },
                'source': {
                    'site_id': cls._site_id,
                    'rack_id': cls._rack_id,
                    'node_id': cls._node_id,
                    'component': cls._component,
                    'module': module
                    },
                'contents': {
                    'event': event_id,
                    'message': message_blob
                }
            }
        })

        cls._producer.send([alert])
        Log.debug("alert sent: %s" % alert)

    @classmethod
    def subscribe(cls, component: str,\
        cluster_conf: str = 'yaml:///etc/cortx/cluster.conf', **filters):
        """
        Subscribe to IEM alerts

        Parameters:
        component       Component that generates the IEM. For e.g. 'S3', 'SSPL'
        cluster_conf    ConfStore URL of cluster.conf file
        """
        if component is None:
            Log.error("Invalid component type: %s" % component)
            raise EventMessageError(errno.EINVAL, "Invalid component type: %s", \
               component)

        cls._consumer = MessageConsumer(consumer_id='event_consumer', \
            consumer_group=component, message_types=['IEM'], \
            auto_ack=True, offset='earliest', cluster_conf=cluster_conf)
        Log.info("IEM Consumer initialized for component: %s" % component)


    @classmethod
    def receive(cls):
        """ Receive IEM alert message """
        cls._initiate_logger()
        if cls._consumer is None:
            Log.error("IEM Consumer is not subscribed")
            raise EventMessageError(errors.ERR_SERVICE_NOT_INITIALIZED, \
                "Consumer is not subscribed")

        alert = cls._consumer.receive()
        Log.debug("Recieved alert: %s" % alert)

        if alert is not None:
            try:
                return json.loads(alert.decode('utf-8'))
            except Exception as e:
                Log.error("unable to parse alert json")
                raise EventMessageError(errno.EPERM, "Unable to load the json. \
                    %s", e)
        return alert
