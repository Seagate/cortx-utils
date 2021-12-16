#include<string.h>
#include<list>
#include<iostream>

class MessageBusClient{
public:
	void send(std::list<std::string> messages);
	void receive();
	void ack();


};

class MessageProducer : public MessageBusClient{

private:
	std::string producer_id;
	std::string message_type;
	std::string method;
public:
	MessageProducer(std::string prod_id,std::string msg_type,std::string meth);

};
class MessageBusAdmin : public MessageBusClient{

};

class MessageConsumer : public MessageBusClient{

};
