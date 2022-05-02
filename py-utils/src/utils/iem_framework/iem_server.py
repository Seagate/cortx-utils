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
from aiohttp import web
from cortx.utils.utils_server import MessageServer
from cortx.utils.iem_framework import EventMessage
from cortx.utils.utils_server.error import RestServerError
from cortx.utils.iem_framework.error import EventMessageError
from cortx.utils.log import Log

routes = web.RouteTableDef()


class IemRequestHandler(MessageServer):
    """ Rest interface of Iem """
    cluster_id = None
    message_server_endpoints = None

    @staticmethod
    async def send(request):
        try:
            payload = await request.json()

            component = payload['component']
            source = payload['source']
            EventMessage.init(component=component, source=source,\
                cluster_id=IemRequestHandler.cluster_id,\
                message_server_endpoints=IemRequestHandler.message_server_endpoints)

            del payload['component']
            del payload['source']
            EventMessage.send(**payload)
        except EventMessageError as e:
            status_code = e.rc
            error_message = e.desc
            Log.error(f"Unable to send event message for component: " \
                      f"{component}, status code: {status_code}," \
                      f" error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                ['EventMessageError', {'message': error_message}]}
        except Exception as e:
            exception_key = type(e).__name__
            exception = RestServerError(exception_key).http_error()
            status_code = exception[0]
            error_message = exception[1]
            Log.error(f"Internal error while sending event messages for " \
                f"component: {component}, status code: " \
                f"{status_code}, error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                [exception_key, {'message': error_message}]}
            raise EventMessageError(status_code, error_message) from e
        else:
            status_code = 200  # No exception, Success
            response_obj = {'status_code': status_code, 'status': 'success'}
            Log.debug(f"POST method finished for component: {component} "
                f"and source: {source}, with status code: {status_code}")
        finally:
            return web.Response(text=json.dumps(response_obj), \
                status=status_code)

    @staticmethod
    async def receive(request):
        Log.debug(f"Received GET request for component " \
            f"{request.rel_url.query['component']}")
        try:
            component = request.rel_url.query['component']
            EventMessage.subscribe(component=component,\
                message_server_endpoints=\
                IemRequestHandler.message_server_endpoints)
            alert = EventMessage.receive()
        except EventMessageError as e:
            status_code = e.rc
            error_message = e.desc
            Log.error(f"Unable to receive event message for component: " \
                f"{component}, status code: {status_code}," \
                f" error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                ['EventMessageError', {'message': error_message}]}
        except Exception as e:
            exception_key = type(e).__name__
            exception = RestServerError(exception_key).http_error()
            status_code = exception[0]
            error_message = exception[1]
            Log.error(f"Internal error while receiving event messages for " \
                f"component: {component}, status code: " \
                f"{status_code}, error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                [exception_key, {'message': error_message}]}
            raise EventMessageError(status_code, error_message) from e
        else:
            status_code = 200  # No exception, Success
            response_obj = {'alert': alert}
            Log.debug(f"GET method finished with status code: {status_code}" \
                f"for component {component} and received event message " \
                f"alert info. - {alert['iem']['info']}.")
        finally:
            return web.Response(text=json.dumps(response_obj), \
                status=status_code)
