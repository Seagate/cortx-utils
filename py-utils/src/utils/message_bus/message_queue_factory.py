#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

from src.template import Factory
from src.utils.message_bus.kafka_message_broker import KafkaMessageBroker
from src.utils.message_bus.config import MessageBusConfig

'''This module helps us to read Queue specific configurations 
    and generate Queue specific administrators'''

class KafkaFactory(Factory):
    '''
    why kafka factory
    class MessageFactory
    Glue layer to create different types of Message Queues
    '''

    def __init__(self):
        config = MessageBusConfig()
        self.config = config.get_config()
        self.adapter = KafkaMessageBroker(self.config)
        self.admin = self.adapter.create_admin()


class RabbitMQFactory(Factory):
    def __init__(self):
        pass