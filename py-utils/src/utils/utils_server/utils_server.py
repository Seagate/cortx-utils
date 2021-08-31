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

from aiohttp import web
from cortx.utils.log import Log


class RestServer:
    """ Base class for Cortx Rest Server implementation """

    def __init__(self):
        app = web.Application()
        from cortx.utils.iem_framework import IemRequestHandler
        from cortx.utils.message_bus import MessageBusRequestHandler
        app.add_routes([web.post('/EventMessage/event', IemRequestHandler.send), \
            web.get('/EventMessage/event', IemRequestHandler.receive), \
            web.post('/MessageBus/message/{message_type}', \
            MessageBusRequestHandler.send), \
            web.get('/MessageBus/message/{message_type}', \
            MessageBusRequestHandler.receive)])

        Log.info("Starting Message Server 127.0.0.1 on port 28300")
        web.run_app(app, host='127.0.0.1', port=28300)


if __name__ == '__main__':
    import os
    from cortx.utils.conf_store import Conf

    Conf.load('config_file', 'json:///etc/cortx/cortx.conf', skip_reload=True)
    # Get the log path
    log_dir = Conf.get('config_file', 'log_dir')
    utils_log_path = os.path.join(log_dir, 'cortx/utils/utils_server')
    # Get the log level
    log_level = Conf.get('config_file', 'utils>log_level', 'INFO')

    Log.init('utils_server', utils_log_path, level=log_level, backup_count=5, \
        file_size_in_mb=5)
    RestServer()