#!/bin/env python3

import sys
from cortx.utils.conf_store import ConfStore

conf_file = sys.argv[1]
op = sys.argv[2]
key = sys.argv[3]

cs = ConfStore()
cs.load('global', conf_file)

if op == "set":
    val = sys.argv[4]
    cs.set('global', key, val)
elif op == "get":
    val = cs.get('global', key)
    print(val)
elif op == "delete":
    cs.delete('global', key)
    
print(cs.keys())
