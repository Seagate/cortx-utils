#include <iostream>
#include <vector>

#include "RestClient.hpp"

int main(int argc, char* argv[])
{
    if ((argc > 4) || (argc < 3))
    {
        std::cout << "Usage: ./a.out [HTTP Verb] [endpoint] [body(optional)]" << std::endl;
        return -1;
    }
    else
    {
        std::string httpVerb = argv[1];
        auto endpoint = argv[2];
        auto body = ((argc == 4) ? argv[3] : "");

        restClient rc(endpoint);
        std::string ret = rc.init();

        if (ret != "")
        {
            std::cout << "Init failed: " << ret << std::endl;
            return -1;
        }

        ret = rc.createAndConnect();

        if (ret != "")
        {
            std::cout << "createAndConnect() failed: " << ret << std::endl;
            return -1;
        }

        char choice;

        while (true)
        {
            std::cout << "Are there any additional headers?(y/n)" << std::endl;
            std::cin >> choice;

            if ((choice == 'n') || (choice == 'N'))
            {
                break;
            }

            std::string key, value;

            std::cout << "Enter key: ";
            std::cin >> key;
            std::cout << "Enter value: ";
            std::cin >> value;

            rc.updateHeader(key, value);
        }

        ret = rc.sendRequest(httpVerb, body);

        if (ret != "")
        {
            std::cout << "sendRequest() failed: " << ret << std::endl;
            return -1;
        }
        
        std::vector<char> data;
        int size = 0;

        ret = rc.readResponse(data, size);

        if (ret != "")
        {
            std::cout << "readResponse failed: " << ret << std::endl;
        }

        std::cout << "Response:" << std::endl;
        for (int i = 0; i < size; i++)
        {
            std::cout << data[i];
        }
        std::cout << std::endl;

        return 0;
    }
}