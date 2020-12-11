from src.utils.message_bus.kafka_message_broker import KafkaMessageBroker
from src.utils.schema import Conf
from src.utils.message_bus.exceptions import MessageBusError


class MessageBrokerFactory:
    """
    A Glue layer to create different types of Message Queues.

    This module helps us to read Queue specific configurations
    and generate Queue specific administrators.
    """
    def __init__(self, message_broker):
        try:
            self.message_broker = message_broker
            self._MAP = {
                "kafka": KafkaMessageBroker
            }
            self.adapter = self.get_adapter()
            self.admin = self.adapter.create_admin()
        except Exception as e:
            raise MessageBusError(f"Invalid Broker. {e}")

    def get_adapter(self):
        return self._MAP[self.message_broker](Conf)
