#include <string.h>
#include <list>
#include <iostream>

class MessageBus{

private:
	MessageBus(){}
public:
	static MessageBus &getInstance();


};
