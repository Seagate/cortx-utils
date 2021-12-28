#pragma once
#include<string.h>
#include<list>
#include<iostream>
#include "message_broker.h"

class MessageBus{

private:
        MessageBus(){}
        //MessageBus(MessageBus const&);
        //void operator=(MessageBus const &);
public:
        MessageBus(MessageBus const&) = delete;
        void operator=(MessageBus const &) = delete;
        static MessageBus &getInstance()
	{
		static MessageBus instance;
		return instance;
	}
        void send(std::string client_id,std::string message_type,std::string method,std::list<std::string> messages)
	{
		 MessageBrokerFactory *mbf = MessageBrokerFactory::create("kafka");
        	 mbf->send(client_id,message_type,method,messages);
	}
	std::list<std::string> receive(std::string client_id)
	{
		 MessageBrokerFactory *mbf = MessageBrokerFactory::create("kafka");
		 mbf->receive(client_id);
	}

	


};
class MessageBusClient{
public:
	MessageBusClient();
	void send(std::list<std::string> messages);
	std::list<std::string> receive();
//	void ack();
private:
//	MessageBus &mb;
	std::string get_conf(std::string key);

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
private:
        std::string consumer_id;
	std::string consumer_group;
        std::list<std::string> message_type;
        std::string offset;
	std::string auto_ack;
public:
        MessageConsumer(std::string cons_id,std::string cons_grp,std::list<std::string> msg_type,std::string offs,std::string aut_ac);

};
