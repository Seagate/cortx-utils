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

from cortx.utils.message_bus import MessageConsumer, MessageProducer
from cortx.utils.message_bus.error import MessageServerError
from cortx.utils.rest_server import RestServer
from cortx.utils.rest_server.error import RestServerError

from aiohttp import web
import json

routes = web.RouteTableDef()


class MessageBusRestServer(RestServer):
    """ Rest interface of message bus """

    _message_bus_ip = '127.0.0.1'
    _message_bus_port = 28300

    def __init__(self):
        super().__init__(web, routes, self._message_bus_ip, \
            self._message_bus_port)

    @staticmethod
    @routes.get('/MessageBus/{message_type}')
    @routes.post('/MessageBus/{message_type}')
    async def message_bus_rest(request):
        if request.method == 'POST':
            try:
                message_type = request.match_info['message_type']
                payload = await request.json()
                messages = payload['messages']
                producer = MessageProducer(producer_id='rest_producer', \
                    message_type=message_type, method='sync')

                producer.send(messages)
            except Exception as e:
                exception_key = type(e).__name__
                status_code = RestServerError(exception_key).http_error()
                response_obj = {'status_code': status_code, 'exception': [exception_key, {'message' : str(e)}]}
                raise MessageServerError(status_code, str(e)) from e
            else:
                status_code = 200 # No exception, Success
                response_obj = {'status_code': status_code, 'status': 'success'}
            finally:
                return web.Response(text=json.dumps(response_obj) , status=status_code)

        if request.method == 'GET':
            try:
                message_types = str(request.match_info['message_type']).split('&')
                consumer_group = request.rel_url.query['consumer_group']
                consumer = MessageConsumer(consumer_id='rest_consumer', \
                    consumer_group=consumer_group, message_types=message_types, \
                    auto_ack=True, offset='latest')

                message = consumer.receive()
            except Exception as e:
                exception_key = type(e).__name__
                status_code = RestServerError(exception_key).http_error()
                response_obj = {'status_code': status_code, 'exception': [exception_key, {'message' : str(e)}]}
                raise MessageServerError(status, str(e)) from e
            else:
                status_code = 200  # No exception, Success
                response_obj = {'messages': str(message)}
            finally:
                return web.Response(text=json.dumps(response_obj), status=status_code)

if __name__ == '__main__':
    MessageBusRestServer()

