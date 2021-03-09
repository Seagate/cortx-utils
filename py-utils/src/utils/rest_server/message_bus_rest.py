#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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

import errno
from flask import Flask, request, jsonify
from cortx.utils.message_bus import MessageBus, MessageProducer, MessageConsumer
from cortx.utils.rest_server.error import RestServerError

app = Flask(__name__)
message_bus = MessageBus()


@app.route('/MessageBus/<message_type>', methods=['GET', 'POST'])
def message_bus_rest(message_type: str):
    """ Rest interface of message bus"""
    if request.method == 'POST':
        try:
            messages = request.json['messages']
            producer = MessageProducer(message_bus, producer_id='rest_producer', \
                message_type=message_type)

            producer.send(messages)
            return jsonify({"status": "Success"})
        except Exception as e:
            raise RestServerError(errno.EINVAL, "Unable to send messages \
                through rest server. %s", e)

    if request.method == 'GET':
        try:
            message_types = message_type.split('&')
            consumer_group = request.args.get('consumer_group')
            consumer = MessageConsumer(message_bus, consumer_id='rest_consumer', \
                consumer_group=consumer_group, message_types=message_types, \
                auto_ack=True, offset='latest')

            message = consumer.receive()
            return jsonify({"message": str(message)})
        except Exception as e:
            raise RestServerError(errno.EINVAL, "Unable to receive messages \
                through rest server. %s", e)


if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=28300)