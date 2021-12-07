#include <iostream>
#include <cstring>
#include <sstream>
#include <fstream>
#include <string>
#include <vector>

#include <ctype.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <unistd.h>

using namespace std;

class restClient
{
    int sock;
    struct sockaddr_in client;
    std::string hostName, port, resource;
    struct hostent *host;
    std::vector<std::pair<std::string, std::string>> headers;

    public:

    restClient(std::string endpoint)
    {
        auto index = endpoint.find("://");
        endpoint = ((index == -1) ? endpoint : endpoint.substr(index + 3));

        index = endpoint.find(":");
        hostName = endpoint.substr(0, index);
        endpoint = endpoint.substr(index + 1);

        index = endpoint.find("/");
        port = endpoint.substr(0, index);
        endpoint = endpoint.substr(index);

        resource = endpoint;

        sock = -1;
        host = NULL;
        bzero(&client, sizeof(client));
    }

    // Sets sockaddr_in and host header
    std::string init()
    {
        if (hostName != "")
        {
            host = gethostbyname(hostName.c_str());

            if ((host == NULL) || (host->h_addr == NULL))
            {
                return "Error retrieving DNS information.";
            }

            client.sin_family = AF_INET;
            client.sin_port = htons(std::atoi(port.c_str()));
            memcpy(&client.sin_addr, host->h_addr, host->h_length);

            headers.push_back({"Host", hostName + ":" + port});
            headers.push_back({"Accept", "*/*"});
        }
        else
        {
            return "Set a Valid Address or Port Number";
        }

        return std::string();
    }

    // To create and connect to socket
    std::string createAndConnect()
    {
        sock = socket(AF_INET, SOCK_STREAM, 0);

        if (sock < 0)
        {
            return "Error at creating socket";
        }

        int ret = connect(sock, (struct sockaddr *)&client, sizeof(client));

        if (ret < 0)
        {
            return "Error while establishing connection" + std::to_string(errno);
        }

        return std::string();
    }

    // To add additional headers
    void updateHeader(const std::string& key, const std::string& value)
    {
        if ((key != "") && (value != ""))
        {
            headers.push_back({key, value});
        }
    }

    // send request
    std::string sendRequest(const std::string& verb, const std::string& body)
    {
        if (body != "")
        {
            headers.push_back({"Content-Length", std::to_string(body.size())});
        }

        stringstream ss;
        ss << verb << " " << resource << " HTTP/1.1\r\n";

        for (auto it : headers)
        {
            ss << it.first << ": " << it.second << "\r\n";
        }
        
        ss << "\r\n";
        ss << body << "\r\n";

        std::string request = ss.str();

        int ret = send(sock, request.c_str(), request.length(), 0);

        if (ret != (int)request.length()) 
        {
            return "Error sending request." + std::to_string(errno);
        }

        return std::string();
    }

    // To recieve response
    std::string readResponse(std::vector<char>& data, int& size)
    {
        while(true)
        {
            char buf[1024] = {'\0'};
            auto valRead = read(sock, buf, 1024);

            if (valRead > 0)
            {
                data.insert(data.end(), buf, buf + valRead);
                size += valRead;
            }
            else if (valRead == 0)
            {
                break;
            }
            else
            {
                return "Error while reading response: " + std::to_string(errno);
            }
        }

        return std::string();
    }

    ~restClient()
    {
        if (sock >= 0)
        {
            close(sock);
        }
        if (host != NULL)
        {
            endhostent();
        }
    }
};