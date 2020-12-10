#!/bin/env python3

""" Sample Test File - TODO - To move to test """

import sys
from cortx.utils.conf_store import ConfStore

conf_file = 'json:/tmp/file1.json'

cs = ConfStore()
cs.load('global', conf_file)

key = "key1"
val = "val1"
print(f"## test1: set {key} {val}")
cs.set('global', key, val)
print("keys: %s" %cs.get_keys('global'))

print(f"## test2: get {key}")
rval = cs.get('global', key)
if val != rval:
    raise Exception("val: %s != %s" %(val, rval))
print(f"rval = {rval}")

print(f"## test3: copy to backup")
cs.load('backup', f"{conf_file}.bak")
cs.copy('global', 'backup')
print("backup: keys: %s" %cs.get_keys('backup'))
cs.save('backup')
    
#print(cs.get_keys('global'))
#print(cs.get_keys('backup'))

print(f"## test4: delete key {key}")
cs.delete('global', key)
print("keys: %s" %cs.get_keys('global'))
