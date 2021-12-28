#include "message_bus_client.h"
//#include "message_bus.h"
#include <string.h>
#include <iterator>
#include <list>

MessageBusClient::MessageBusClient(){
//	MessageBus &mb= NULL;
//	&mb = MessageBus::getInstance();

}
void MessageBusClient::send(std::list<std::string> messages)
{
	//std::list<std::string>::iterator s;
	MessageBus *MyMessageBus = &MessageBus::getInstance();
	//MessageBus::getInstance.send("","message_bus_test","",messages);
	MyMessageBus->send("","message_bus_test","",messages);
	//for(s= messages.begin();s!=messages.end();s++)
	//	std::cout<<*s<<" ";
}
std::list<std::string> MessageBusClient::receive()
{
	MessageBus *MyMessageBus = &MessageBus::getInstance();
	MyMessageBus->receive("");
}
std::string MessageBusClient::get_conf(std::string key)
{


}
//void MessageBusClient::receive(){}
//void MessageBusClient::ack(){}
//void MessageBusClient::delete_(){}

MessageProducer::MessageProducer(std::string prod_id,std::string msg_type,std::string meth)
{
	MessageBusClient client;
	//&mb = MessageBus::getInstance();
	producer_id = prod_id; // example csm
	message_type = msg_type;  // topic
	method = meth; // sync and async

}
MessageConsumer::MessageConsumer(std::string cons_id,std::string cons_grp,std::list<std::string> msg_type,std::string offs,std::string aut_ac)
{
	consumer_id = cons_id;
	consumer_group = cons_grp;
	offset = offs;
	auto_ack = aut_ac;

}

