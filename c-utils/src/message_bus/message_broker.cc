 #include "message_broker.h"
#include<string.h>
//#include "message_broker_collection.h"


MessageBrokerFactory* MessageBrokerFactory::create(std::string type)
{

if(type == "kafka")
	return new KafkaMessageBroker();

}
