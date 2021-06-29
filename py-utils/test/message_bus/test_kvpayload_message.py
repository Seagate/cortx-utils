#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import json
import unittest
from cortx.utils.kv_store import KvPayload
from cortx.utils.message_bus import MessageProducer, MessageConsumer


class TestKVPayloadMessage(unittest.TestCase):
    """ Test Send/Receive KvPayload as message """

    _message_type = 'kv_payloads'
    _payload = KvPayload({'message_broker': {'type': 'kafka', 'cluster': \
        [{'server': 'localhost', 'port': '9092'}]}})
    _consumer = MessageConsumer(consumer_id='kv_consumer', consumer_group='kv', \
        message_types=[_message_type], auto_ack=True, offset='earliest')
    _producer = MessageProducer(producer_id='kv_producer', \
        message_type=_message_type, method='sync')

    def test_json_kv_send(self):
        """ Load json as payload """
        message = TestKVPayloadMessage._payload.get_data()
        TestKVPayloadMessage._producer.send([json.dumps(message)])

    def test_json_receive(self):
        """ Receive json payload as message """
        message = TestKVPayloadMessage._consumer.receive()
        self.assertTrue(message.decode('utf-8'), str({'message_broker': \
            {'type': 'kafka', 'cluster': [{'server': 'localhost', 'port': \
            '9092'}]}}))

    def test_yaml_kv_send(self):
        """ Load yaml as payload """
        message = TestKVPayloadMessage._payload.get_data(format_type='yaml')
        TestKVPayloadMessage._producer.send([message])

    def test_yaml_receive(self):
        """ Receive json payload as message """
        message = TestKVPayloadMessage._consumer.receive()
        self.assertTrue(message.decode('utf-8'), "message_broker:\n  \
            cluster:\n  - port: '9092'\n    server: localhost\n  type: kafka\n")

    def test_toml_kv_send(self):
        """ Load toml as payload """
        message = TestKVPayloadMessage._payload.get_data(format_type='toml')
        TestKVPayloadMessage._producer.send([message])

    def test_toml_receive(self):
        """ Receive json payload as message """
        message = TestKVPayloadMessage._consumer.receive()
        self.assertTrue(message.decode('utf-8'), '[message_broker]\ntype = \
            "kafka"\n[[message_broker.cluster]]\nserver = "localhost"\nport = \
            "9092"\n\n')


if __name__ == '__main__':
    unittest.main()