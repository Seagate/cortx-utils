#! /bin/bash
# ./update_hosts server1 server2

sed -i "s/<SRVNODE-1_HOST>/$1/g" inventories/hw_deployment/hosts
sed -i "s/<SRVNODE-2_HOST>/$2/g" inventories/hw_deployment/hosts