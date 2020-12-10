from src.utils.message_bus.kafka_message_broker import KafkaMessageBroker
from src.utils.message_bus.config import MessageBusConfig

class MessageBrokerFactory():
    """
    A Glue layer to create different types of Message Queues.

    This module helps us to read Queue specific configurations
    and generate Queue specific administrators.
    """
    def __init__(self, message_broker):
        #Read the config
        config = MessageBusConfig()
        self.config = config.get_config()
        if message_broker == 'kafka':
            self.adapter = KafkaMessageBroker(self.config)
        self.admin = self.adapter.create_admin()
