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

from src.utils.message_bus import MessageBusClient


class MessageConsumer(MessageBusClient):

    def __init__(self, message_bus, consumer_id=None, consumer_group=None, message_type=None, offset=None):
        """ Initialize a Message Consumer

        Keyword Arguments:
            message_bus: An instance of message bus class.
            consumer_group: A String that represents Consumer Group ID.
                    Group of consumers can process messages
            message_type: This is essentially equivalent to the queue/topic name.
                    For e.g. ["Alert"]
            offset: Can be set to "earliest" (default) or "latest".
                    ("earliest" will cause messages to be read from the beginning)
        """
        super().__init__(message_bus, 'CONSUMER', client_id=consumer_id,
                         consumer_group=consumer_group, message_type=message_type,
                         offset=offset)

    def receive(self):
        """ Receives the messages """
        return super().receive()
