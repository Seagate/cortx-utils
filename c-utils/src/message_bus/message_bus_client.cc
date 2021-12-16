#include "message_bus_client.h"
#include <string.h>
#include <iterator>
#include <list>

//MessageBusClient::MessageBusClient(){}
void MessageBusClient::send(std::list<std::string> messages)
{
	std::list<std::string>::iterator s;
	for(s= messages.begin();s!=messages.end();s++)
		std::cout<<*s<<" ";
}
void MessageBusClient::receive(){}
void MessageBusClient::ack(){}
//void MessageBusClient::delete_(){}

MessageProducer::MessageProducer(std::string prod_id,std::string msg_type,std::string meth)
{
	producer_id = prod_id;
	message_type = msg_type;
	method = meth;

}

