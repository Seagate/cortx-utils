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

class BusCallback():
    
    def precreate_busclient(self, role):
        pass

    def postcreate_busclient(self, role):
        pass

    def precreate_topic(self, topic_name, timeout_ms=None, validate_only=False):
        pass

    def postcreate_topic(self, topic_name, timeout_ms=None, validate_only=False):
        pass

    def pre_send(self, clnt, topic, msg):
        pass

    def post_send(self, clnt, topic, msg):
        pass

    def pre_receive(self, consumer):
        pass

    def post_receive(self, consumer):
        pass

    def pre_subscribe(self, consumer, topic, pattern=None, listener=None):
        pass

    def post_subscribe(self, consumer, topic, pattern=None, listener=None):
        pass


class MyCallback(BusCallback):
    
    def precreate_busclient(self, role):
        super().precreate_busclient(role)

    def postcreate_busclient(self, role):
        super().postcreate_busclient(role)
    
    def precreate_topic(self, topic_name, timeout_ms=None, validate_only=False):
        super().precreate_topic(topic_name, timeout_ms=None, validate_only=False)
        
    def postcreate_topic(self, topic_name, timeout_ms=None, validate_only=False):
        super().postcreate_topic(topic_name, timeout_ms=None, validate_only=False)
    
    def pre_send(self, clnt, topic, msg):
        super().pre_send(clnt, topic, msg)

    def post_send(self, clnt, topic, msg):
        super().post_send(clnt, topic, msg)
        
    def pre_subscribe(self, consumer, topic, pattern=None, listener=None):
        super().pre_subscribe(consumer, topic, pattern=None, listener=None)

    def post_subscribe(self, consumer, topic, pattern=None, listener=None):
        super().post_subscribe(consumer, topic, pattern=None, listener=None)

    def pre_receive(self,consumer):
        super().pre_receive(consumer)

    def post_receive(self, consumer):
        super().pre_receive(consumer)