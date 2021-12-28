#pragma once
#include <string.h>
#include <list>
#include <iostream>
#include <librdkafka/rdkafka.h>
class MessageBrokerFactory{

public:
//	MessageBrokerFactory(){}
	virtual void send(std::string,std::string,std::string,std::list<std::string>) = 0;

	virtual std::list<std::string> receive(std::string client_id) = 0;
//	virtual void ack() = 0;
	static MessageBrokerFactory *create(std::string type);
};
class KafkaMessageBroker : public MessageBrokerFactory{
private:
//      void dr_msg_cb(rd_kafka_t *rk, const rd_kafka_message_t *rkmessage, void *opaque);
public:
        KafkaMessageBroker();
        void send(std::string producer_id,std::string message_type,std::string method,std::list<std::string> messages);
	std::list<std::string> receive(std::string client_id);

};

