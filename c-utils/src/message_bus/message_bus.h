#include <string.h>
#include <list>
#include <iostream>

class MessageBus{

private:
	MessageBus(){}
	//MessageBus(MessageBus const&);
	//void operator=(MessageBus const &);
public:
	MessageBus(MessageBus const&) = delete;
	void operator=(MessageBus const &) = delete;
	static MessageBus &getInstance();
	void send(std::string client_id,std::string message_type,std::string method,std::list<std::string> messages);
	std::list<std::string> receive();

};
