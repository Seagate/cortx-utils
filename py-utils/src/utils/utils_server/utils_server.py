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

import argparse
import errno
from argparse import RawTextHelpFormatter
from aiohttp import web

from cortx.utils.log import Log
from cortx.utils.common import CortxConf
from cortx.utils.conf_store import Conf
from cortx.utils.errors import UtilsError
from cortx.utils.message_bus import MessageBus


class UtilsServerError(UtilsError):
    """UtilsServerError exception with error code and output."""
    def __init__(self, rc, message, *args):
        super().__init__(rc, message, *args)


class UtilsServer:
    """Base class for Cortx Rest Server implementation."""
    def __init__(self):
        self.app = web.Application()

    def run_app(self, web):
       Log.info("Starting Message Server 0.0.0.0 on port 28300")
       web.run_app(self.app, port=28300)


class MessageServer(UtilsServer):
    """Base class for Cortx Rest Server implementation."""
    def __init__(self, message_server_endpoints):
        super().__init__()
        MessageBus.init(message_server_endpoints=message_server_endpoints)
        from cortx.utils.iem_framework import IemRequestHandler
        from cortx.utils.message_bus import MessageBusRequestHandler
        from cortx.utils.audit_log import AuditLogRequestHandler
        self.app.add_routes([web.post('/EventMessage/event', IemRequestHandler.send), \
            web.get('/EventMessage/event', IemRequestHandler.receive), \
            web.post('/MessageBus/message/{message_type}', \
            MessageBusRequestHandler.send), \
            web.get('/MessageBus/message/{message_type}', \
            MessageBusRequestHandler.receive),
            web.post('/AuditLog/message/', \
            AuditLogRequestHandler.send),
            web.post('/AuditLog/webhook/', \
            AuditLogRequestHandler.send_webhook_info)
            ])
        super().run_app(web)


if __name__ == '__main__':
    from cortx.utils.conf_store import Conf
    parser = argparse.ArgumentParser(description='Utils server CLI',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('-c', '--config', dest='cluster_conf',\
        help="Cluster config file path for Support Bundle",\
        default='yaml:///etc/cortx/cluster.conf')
    args=parser.parse_args()
    cluster_conf = args.cluster_conf
    Conf.load('config', cluster_conf, skip_reload=True)
    CortxConf.init(cluster_conf=cluster_conf)
    # Get the log path
    log_dir = CortxConf.get_storage_path('log')
    if not log_dir:
        raise UtilsServerError(errno.EINVAL, "Fail to initialize logger."+\
            " Unable to find log_dir path entry")
    utils_log_path = CortxConf.get_log_path('utils_server', base_dir=log_dir)
    # Get the log level
    log_level = CortxConf.get('utils>log_level', 'INFO')
    Log.init('utils_server', utils_log_path, level=log_level, backup_count=5, \
        file_size_in_mb=5)
    message_bus_backend = Conf.get('config', 'cortx>utils>message_bus_backend')
    message_server_endpoints = Conf.get('config',\
            f'cortx>external>{message_bus_backend}>endpoints')
    MessageServer(message_server_endpoints)