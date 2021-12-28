#include "message_bus_client.h"
#include <string.h>
#include<list>


void produce_message()
{
        MessageProducer mp("ip_addr","topic_name","test");
        //Producer id, message_type,method
        std::list<std::string> l;
        std::string test1 = "Test message 1";
        std::string test2= "Test message 2";
        l.push_back(test1);
        l.push_back(test2);
        mp.send(l);


}

std::list<std::string> consume_message()
{
	std::string test1 = "topic1";
        std::string test2= "topic2";
        std::list<std::string> l;
        l.push_back(test1);
        l.push_back(test2);

	MessageConsumer mc("test","test",l,"offset","ack");
	//consumer_id,consumer_group,list of topics,offset,auto ack
	std:list<std::string> res	= mc.receive();
	return res;

}
int main()
{
	std::list<std::string> result;

	produce_message();
	result = consume_message();

	return 0;
}
