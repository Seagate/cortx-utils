import sys
import argparse
import errno

from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfStoreError

parser = argparse.ArgumentParser(description='ConfStore CLI')

parser.add_argument("url", help="Location of the config file")
parser.add_argument("command", help="Command could be get()/ set()/ delete()",
                    choices=['get', 'set', 'delete'], type=str)
parser.add_argument("key_value", help="key_value could be a list of single or"
                    " nested. single - key1=value1 nested key1>key2=value2 "
                    "key1=value1;key2=value2")

args = parser.parse_args()
index = 'conf_cli'
Conf.load(index, args.url)

command = args.command
key_val = args.key_value
key_val_lst = key_val.split(';')


if command == "set":
    key_val_dict = {}

    for each in key_val_lst:
        if len(each.split('=')) > 1:
            key_val_dict[each.split('=')[0]] = each.split('=')[1]
        else:
            raise ConfStoreError(errno.EINVAL,
                                 "key or values should not be empty %s", each)
    for key, value in key_val_dict.items():
        Conf.set(index, key, value)
    Conf.save(index)

elif command == "get":
    for key in key_val_lst:
        vals = Conf.get(index, key)
        print(vals)

elif command == 'get_keys':
    keys = Conf.get_keys(index)
    print(keys)

elif command == "delete":
    for key in key_val_lst:
        Conf.delete(index, key)
    Conf.save(index)
