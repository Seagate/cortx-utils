#include <string.h>
#include <list>
#include <iostream>

class MessageBrokerFactory{

public:
	virtual void send() = 0;
	virtual void receive() = 0;
	virtual void ack() = 0;
	static MessageBrokerFactory *create(std::string type);
};
class MessageBroker:public MessageBrokerFactory{

public:
	void send();
	void receive();
	void ack();

};
