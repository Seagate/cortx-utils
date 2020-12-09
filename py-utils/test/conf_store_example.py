import sys
sys.path.insert(1, '../')

from src.utils.conf_store import ConfStore, KvStorageFactory, KvStore


def example_function(path):
    # local / global
    conf = ConfStore('local')
    # conf = ConfStore()
    kv_store_backend = KvStorageFactory(path)
    # conf_backend = KvStore(kv_store_backend)
    # conf_backend = KvStore(KvStorageFactory('salt://prefix'))
    # conf_backend = KvStore(KvStorageFactory('console://prefix'))
    conf.load(index='sspl', store = kv_store_backend)
    return conf
    


conf_1 = example_function('/home/centos/sspl.json')
# conf_2 = example_function('console://prefix')
v1 = conf_1.get('1sspl.stats.health')
print(v1)