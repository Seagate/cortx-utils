import sys

sys.path.insert(1, '../../')

from src.utils.conf_store import ConfStore, KvStoreFactory
from src.utils.kv_store import KvStore

# Init ConfStore
conf = ConfStore('local')

def load_config(index, backend_url):
    # Instantiate and Load Config
    conf_backend = KvStoreFactory(backend_url)
    conf.load(index, kvstore=KvStore(conf_backend))
    return conf

# Load configs
load_config('sspl_local', 'file:///home/centos/sspl.json')
# load_config('sspl_global', 'console://consule.xyz.com:5050/sspl')

# Use Configuration
user_name = conf.get('sspl_local', 'management.user', default_value=None)
management = conf.get('sspl_local', default_value=None)
# conf.setter('sspl_local', ['new', 'join'], ['value', 'kumar'])
# updated = conf.get('sspl_local', default_value=None)
# enclosure_ip = conf.get('sspl_global', 'enclosure.ip', default_value='127.0.0.1')

# save the config by index

# conf.save('sspl_local')

print(user_name)
print(management)
# print(updated)