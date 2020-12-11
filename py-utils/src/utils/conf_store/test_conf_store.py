#!/bin/env python3

""" Sample Test File - TODO - To move to test """

import sys
from cortx.utils.conf_store import ConfStore

conf_file = 'json:/tmp/file1.json'

cs = ConfStore()
print(f"\n## test: load global {conf_file}")
cs.load('global', conf_file)

key = "key1"
val = "val1"
print(f"\n## test: global set {key} {val}")
cs.set('global', key, val)
print("global keys = %s" %cs.get_keys('global'))

print(f"\n## test: global get {key}")
rval = cs.get('global', key)
if val != rval:
    raise Exception("val: %s != %s" %(val, rval))
print(f"rval = {rval}")

print(f"\n## test: global save")
cs.save('global')

print(f"\n## test: reload global1 {conf_file}")
cs.load('global1', conf_file)

print(f"\n## test: global1 get {key}")
rval = cs.get('global', key)
print(f"global1 rval = {rval}")
print("global1 keys = %s" %cs.get_keys('global1'))

print(f"\n## test: copy to backup")
cs.load('backup', f"{conf_file}.bak")
cs.copy('global', 'backup')
print("backup: keys: %s" %cs.get_keys('backup'))
cs.save('backup')
    
#print(cs.get_keys('global'))
#print(cs.get_keys('backup'))

print(f"\n## test: delete global key {key}")
cs.delete('global', key)
print("keys: %s" %cs.get_keys('global'))
