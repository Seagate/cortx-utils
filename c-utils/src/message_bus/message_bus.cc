#include "message_bus.h"

MessageBus &MessageBus::getInstance()
{
	static MessageBus instance;
	return instance;
}
