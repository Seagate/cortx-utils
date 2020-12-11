#!/bin/env python3

""" Sample Test File - TODO - To move to test """

import sys
from cortx.utils.conf_store import Conf

conf_file = 'json:/tmp/file1.json'

print(f"\n## test: load {conf_file}")
Conf.load('global', conf_file)

key = "key1"
val = "val1"
print(f"\n## test: set {key} {val}")
Conf.set('global', key, val)
print("keys = %s" %Conf.get_keys('global'))

print(f"\n## test: get {key}")
rval = Conf.get('global', key)
if val != rval:
    raise Exception("val: %s != %s" %(val, rval))
print(f"rval = {rval}")

print(f"\n## test: save")
Conf.save('global')

print(f"\n## test: delete key {key}")
Conf.delete('global', key)
print("keys: %s" %Conf.get_keys('global'))
