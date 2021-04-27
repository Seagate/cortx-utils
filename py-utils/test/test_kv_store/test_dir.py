#!/bin/python3

from cortx.utils.kv_store import KvStoreFactory
import sys

url = sys.argv[1]
cmd = sys.argv[2]
kvs = KvStoreFactory.get_instance(url)

if cmd == "set":
    key = sys.argv[3]
    val = sys.argv[4]
    kvs.set([key], [val])

elif cmd == "get":
    key = sys.argv[3]
    vals = kvs.get([key])
    print(vals)

elif cmd == "delete":
    key = sys.argv[3]
    kvs.delete([key])

elif cmd == "get_data":
    format_type = sys.argv[3]
    print(kvs.get_data(format_type))
