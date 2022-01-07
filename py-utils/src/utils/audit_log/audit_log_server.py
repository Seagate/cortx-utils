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

from cortx.utils.utils_server import RestServer
from cortx.utils.audit_log.error import AuditLogError
from cortx.utils.utils_server.error import RestServerError
from cortx.utils.message_bus import MessageProducer
from cortx.utils.log import Log

routes = web.RouteTableDef()
producer = MessageProducer(producer_id='audit_log_send', \
    message_type='audit_messages', method='sync')


class AuditLogRequestHandler(RestServer):
    """Rest interface of Audit log."""
    # webhook_info will be removed once webhook_info store to persistent storage
    webhook_info = None
    @staticmethod
    async def send(request):
        Log.debug("Received POST request for audit message")
        try:
            payload = await request.json()
            messages = payload['messages']
            external_server_info = AuditLogRequestHandler.webhook_info
            # send audit logs messages to to external server provided by webhook
            if external_server_info:
                # write Audit Log messages to the webhook server
                import requests

                data = json.dumps({'messages': messages})
                headers = {'content-type': 'application/json'}
                response = requests.post(url=external_server_info, data=data,\
                    headers=headers)
                if response.status_code != 200:
                    # if status code from webhok server is not 200 then store audit
                    # log message to message bus
                    producer.send(messages)
            else:
                # write the audit log message to message bus
                producer.send(messages)
        except AuditLogError as e:
            status_code = e.rc
            error_message = e.desc
            Log.error(f"Unable to receive audit messages, status code: {status_code}," \
                f" error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                ['AuditLogError', {'message': error_message}]}
        except Exception as e:
            exception_key = type(e).__name__
            exception = RestServerError(exception_key).http_error()
            status_code = exception[0]
            error_message = exception[1]
            Log.error(f"Internal error while receiving audit messages." \
                f"status code: {status_code}, error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                [exception_key, {'message': error_message}]}
            raise AuditLogError(status_code, error_message) from e
        else:
            status_code = 200  # No exception, Success
            response_obj = {}
            Log.debug(f"Receiving audit messages using POST method finished with status"\
                f" code: {status_code}")
            response_obj = {'status_code': status_code, 'status': 'success'}
        finally:
            return web.Response(text=json.dumps(response_obj), \
                status=status_code)

    @staticmethod
    async def send_webhook_info(request):
        Log.debug("Received POST request for webhook information")
        try:
            external_server_info = await request.json()
            # write webhook info to the external server
            AuditLogRequestHandler.webhook_info = external_server_info
            # TODO store webhook_info to persistent storage
        except AuditLogError as e:
            status_code = e.rc
            error_message = e.desc
            Log.error(f"Unable to receive audit webhook information, status code: " \
                f"{status_code}, error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                ['AuditLogError', {'message': error_message}]}
        except Exception as e:
            exception_key = type(e).__name__
            exception = RestServerError(exception_key).http_error()
            status_code = exception[0]
            error_message = exception[1]
            Log.error(f"Internal error while receiving webhook info." \
                f"status code: {status_code}, error: {error_message}")
            response_obj = {'error_code': status_code, 'exception': \
                [exception_key, {'message': error_message}]}
            raise AuditLogError(status_code, error_message) from e
        else:
            status_code = 200  # No exception, Success
            response_obj = {}
            Log.debug(f"Receiving webhook info using POST method finished with status " \
                f"code: {status_code}")
            response_obj = {'status_code': status_code, 'status': 'success'}
        finally:
            return web.Response(text=json.dumps(response_obj), \
                status=status_code)