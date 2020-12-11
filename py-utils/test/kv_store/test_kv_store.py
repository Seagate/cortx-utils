from __future__ import absolute_import
import sys
sys.path.insert(1, '../../')

from src.utils.kv_store import KvStoreFactory

kv_store = KvStoreFactory.get_instance('file:///home/centos/sspl.json')
print(kv_store.load())
print(kv_store.id())