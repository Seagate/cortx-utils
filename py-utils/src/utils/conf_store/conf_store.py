#!/bin/python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import errno
import time

from cortx.utils.conf_store.error import ConfError
from cortx.utils.conf_store.conf_cache import ConfCache
from cortx.utils.kv_store.kv_store import KvStoreFactory
from cortx.utils import errors
import cortx.utils.const as const


class ConfStore:
    """Configuration Store based on the KvStore."""

    def __init__(self, delim='>'):
        """
        ConfStore will be initialized at the time of load.

        delim is used to split key into hierarchy, e.g. "k1>2" or "k1.k2"
        """

        if len(delim) > 1 or delim not in [':', '>', '.', '|', ';', '/']:
            raise ConfError(errno.EINVAL, "invalid delim %s", delim)
        self._delim = delim
        self._cache = {}
        self._callbacks = {}
        self._machine_id = self._get_machine_id()
        self._lock_owner = self._get_machine_id()
        self._lock_domain = const.DEFAULT_LOCK_DOMAIN
        self._lock_duration = const.DEFAULT_LOCK_DURATION

    @property
    def machine_id(self):
        return self._machine_id

    def _get_machine_id(self):
        """Returns the machine id from /etc/machine-id."""
        from pathlib import Path
        machine_id_file = Path("/etc/machine-id")
        if machine_id_file.is_file() and machine_id_file.stat().st_size > 0:
            with open("/etc/machine-id", 'r') as mc_id_file:
                machine_id = mc_id_file.read()
            return machine_id

    def load(self, index: str, kvs_url: str, **kwargs):
        """
        Loads the config from KV Store.

        Parameters:
        index:     Identifier for the config loaded from the KV Store
        kv_store:  KV Store (Conf Backend)
        fail_reload: When True, and if index already exists, load() throws
                     exception.
                     When True, and if index do not exists, load() succeeds.
                     When false, irrespective of index status, load() succeeds
                     Default: True
        skip_reload: When True, it skips reloading a index configuration by
                     overriding fail_reload
                     Default: False
        callback:  Callback for the config changes in the KV Store.
        """
        fail_reload = True
        skip_reload = False
        recurse = True
        for key, val in kwargs.items():
            if key == 'fail_reload':
                fail_reload = val
            elif key == 'skip_reload':
                skip_reload = val
            elif key == 'callback':
                self._callbacks[index] = val
            elif key == 'recurse':
                if val not in [True, False]:
                    raise ConfError(errno.EINVAL, "Invalid value for recurse %s", val)
                recurse = val
            else:
                raise ConfError(errno.EINVAL, "Invalid parameter %s", key)

        if index in self._cache.keys():
            if skip_reload:
                return
            if fail_reload:
                raise ConfError(errno.EINVAL, "conf index %s already exists",
                                index)
        kv_store = KvStoreFactory.get_instance(kvs_url, self._delim)
        self._cache[index] = ConfCache(kv_store, self._delim, recurse=recurse)

    def save(self, index: str):
        """Saves the given index configuration onto KV Store."""
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)

        self._cache[index].dump()

    def get(self, index: str, key: str, default_val: str = None, **filters):
        """
        Obtain value for the given configuration.

        Paraeters:
        index   Configuration Domain ID where config key values are stored
        key     Configuration key. This can take two forms
                1. "xyz" - Top Level Key
                2. "x.y.z" - Key 'z' under x and y. Nested Structure.
        default_val
                Default Value

        Return Value:
                Return type will be dict or string based of key
        """
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)
        if key is None:
            raise ConfError(errno.EINVAL, "can't able to find config key "
                                               "%s in loaded config", key)
        val = self._cache[index].get(key, **filters)
        return default_val if val is None else val

    def set(self, index: str, key: str, val):
        """
        Sets the value into the DB for the given index, key.

        Parameters:
        index   Configuration Domain ID where config key values are stored
        key     Configuration key. This can take two forms
                1. "xyz" - Top Level Key
                2. "x.y.z" - Key 'z' under x and y. Nested Structure.
        val     Value to be set. Can be string or dict
        """
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)

        self._cache[index].set(key, val)

    def get_keys(self, index: str, **filters) -> list:
        """
        Obtains list of keys stored in the specific config store.

        Input Paramters:
        Index   - Index for which the list of keys to be obtained
        Filters - Filters to be applied before the keys to be returned.
                  List of filters:
                  * key_index={True|False} (default: True)
                    when False, returns keys including array index
                    e.g. In case of "xxx[0],xxx[1]", only "xxx" is returned
        """
        return self._cache[index].get_keys(**filters)

    def get_data(self, index: str):
        """Obtains entire config for given index."""
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                                 index)
        return self._cache[index].get_data()

    def delete(self, index: str, key: str, force: bool = False):
        """Delets a given key from the config."""
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)
        return self._cache[index].delete(key, force)

    def search(self, index: str, parent_key: str, search_key: str,
        search_val: str = None) -> list:
        """
        Search for a given value in the conf store.

        Returns list of keys that matched the creteria (i.e. has given value)
        """
        return self._cache[index].search(parent_key, search_key, search_val)

    def add_num_keys(self, index: str):
        """Add "num_xxx" keys for all the list items in ine KV Store."""
        self._cache[index].add_num_keys()

    def copy(self, src_index: str, dst_index: str, key_list: list = None,
        recurse: bool = True):
        """
        Copies one config domain to the other and saves.

        Parameters:
        src_index Source Index
        dst_index Destination Index
        """
        if src_index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                src_index)

        if dst_index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                dst_index)

        if key_list is None:
            if recurse:
                key_list = self._cache[src_index].get_keys(key_index=True)
            else:
                key_list = self._cache[src_index].get_keys(key_index=False)
        for key in key_list:
            self._cache[dst_index].set(key, self._cache[src_index].get(key))

    def compare(self, index1: str, index2: str):
        """
        Compares two configs and returns difference.

        Parameters:
        index1 : Conf Index 1
        index2 : Conf Index 2

        Return Value:
        Returns three lists : New keys, deleted keys, Updated keys
        """
        if index1 not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index1)
        if index2 not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index2)

        key_list1 = self._cache[index1].get_keys()
        key_list2 = self._cache[index2].get_keys()
        deleted_keys = list(set(key_list1).difference(key_list2))
        new_keys = list(set(key_list2).difference(key_list1))
        updated_keys = list(filter(lambda key: key not in deleted_keys and self._cache[index1].get(key) != self._cache[index2].get(key), key_list1))
        return new_keys, deleted_keys, updated_keys

    def merge(self, dest_index: str, src_index: str, keys: list = None):
        """
        Merges the content of src_index and dest_index file.

        Parameters:
        dst_index - Destination Index, to this index resulted values will be
            merged
        src_index - Source Index, From which new keys (and related values) are
            picked up for merging
        keys - optional parameter, Only these keys (and related values) from
            src_index will be merged.
        """
        if src_index not in self._cache.keys():
            raise ConfError(errors.ERR_NOT_INITIALIZED, "config index %s is "\
                "not loaded", src_index)
        if dest_index not in self._cache.keys():
            raise ConfError(errors.ERR_NOT_INITIALIZED, "config index %s is "\
                "not loaded", dest_index)
        if keys is None:
            keys = self._cache[src_index].get_keys()
        else:
            for key in keys:
                if not self._cache[src_index].get(key):
                    raise ConfError(errno.ENOENT, "%s is not present in %s",\
                        key, src_index)
        self._merge(dest_index, src_index, keys)

    def _merge(self, dest_index, src_index, keys):
        for key in keys:
            if key not in self._cache[dest_index].get_keys():
                self._cache[dest_index].set(key, self._cache[src_index].get(key))

    def lock(self, index: str, **kwargs):
        """
        Attempt to acquire the config lock.

        Parameters:
        index(required): Identifier of the config.
        domain(optional): Identity of the lock holder.
        owner(optional): Instance of domain who is sending lock request.
        duration(optional): Obtains the lock for the give duration in terms of seconds.

        return: True if the lock was successfully acquired,
            false if it is already acquired by someone.
        """
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)

        allowed_keys = { 'domain', 'owner', 'duration' }
        for key, val in kwargs.items():
            if key not in allowed_keys:
                raise ConfError(errno.EINVAL, "Invalid parameter %s", key)
            if key == 'duration' and not isinstance(val, int):
                raise ConfError(errno.EINVAL, "Invalid value %s for parameter %s", val, key)

        owner = self._lock_owner if 'owner' not in kwargs else kwargs['owner']
        domain = self._lock_domain if 'domain' not in kwargs else kwargs['domain']
        duration = self._lock_duration if 'duration' not in kwargs else kwargs['duration']

        rc = False
        if self.test_lock(index, owner=owner, domain=domain):
            self.set(index, const.LOCK_OWNER_KEY_PREFIX % domain, owner)
            lock_end_time = time.time() + duration
            self.set(index, const.LOCK_END_TIME_KEY_PREFIX % domain, str(lock_end_time))
            # simulate a timedelay for checking race condition
            time.sleep(0.01)
            # check weather lock requester is same is
            # current lock holder to avoid race condition
            if self.get(index, const.LOCK_OWNER_KEY_PREFIX % domain) == owner:
                rc = True
        return rc

    def unlock(self, index: str, **kwargs):
        """
        Attempt to release the config lock.

        Parameters:
        index(required): Identifier of the config.
        domain(optional): Identity of the Lock Holder.
        owner(optional): Instance of the domain sending  unlock request.
        force(optional, default=False): When true, lock is forcefully released.

        return: True if the lock was successfully released,
            false if it there is no lock or acquired by someone else unless force=true.
        """
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)

        allowed_keys = { 'domain', 'owner', 'force' }
        for key, val in kwargs.items():
            if key not in allowed_keys:
                raise ConfError(errno.EINVAL, "Invalid parameter %s", key)
            if key == 'force' and not isinstance(val, bool):
                raise ConfError(errno.EINVAL, "Invalid value %s for parameter %s", val, key)

        owner = self._lock_owner if 'owner' not in kwargs else kwargs['owner']
        domain = self._lock_domain if 'domain' not in kwargs else kwargs['domain']
        force = False if 'force' not in kwargs else kwargs['force']

        rc = False
        if self.get(index, const.LOCK_OWNER_KEY_PREFIX % domain) == owner or force:
            self.delete(index, const.LOCK_OWNER_KEY_PREFIX % domain)
            self.delete(index, const.LOCK_END_TIME_KEY_PREFIX % domain)
            rc = True
        return rc

    def test_lock(self, index: str, **kwargs):
        """
        Check whether lock is acquired on the config.

        Parameters:
        index(required): param index: Identifier of the config.
        domain(optional): Identity of the Lock Holder.
        owner(optional): Instance of domain who needs to test lock.

        return: True if lock can be acquired by someone else False
        """
        if index not in self._cache.keys():
            raise ConfError(errno.EINVAL, "config index %s is not loaded",
                index)

        allowed_keys = { 'domain' , 'owner'}
        for key, _ in kwargs.items():
            if key not in allowed_keys:
                raise ConfError(errno.EINVAL, "Invalid parameter %s", key)

        owner = self._lock_owner if 'owner' not in kwargs else kwargs['owner']
        domain = self._lock_domain if 'domain' not in kwargs else kwargs['domain']

        _current_owner= self.get(index, const.LOCK_OWNER_KEY_PREFIX % domain)
        if _current_owner in [None, "", owner]:
            return True

        _end_time = self.get(index, const.LOCK_END_TIME_KEY_PREFIX % domain)
        if _end_time in [None, ""]:
            return True

        if float(_end_time) < time.time():
            return True
        return False


class Conf:
    """Singleton class instance based on conf_store."""

    _conf = None
    _delim = '>'
    _machine_id = None

    @staticmethod
    def init(**kwargs):
        """Static init for initialising and setting attributes."""
        if Conf._conf is None:
            for key, val in kwargs.items():
                setattr(Conf, f"_{key}", val)
            Conf._conf = ConfStore(delim=Conf._delim)
            Conf._machine_id = Conf._conf.machine_id

    @staticmethod
    def load(index: str, url: str, recurse=True, **kwargs):
        """Loads Config from the given URL."""
        if Conf._conf is None:
            Conf.init()
        Conf._conf.load(index, url, recurse=recurse, **kwargs)

    @staticmethod
    def save(index: str):
        """Saves the configuration onto the backend store."""
        Conf._conf.save(index)

    @staticmethod
    def set(index: str, key: str, val):
        """Sets config value for the given key."""
        Conf._conf.set(index, key, val)

    @staticmethod
    def get(index: str, key: str, default_val: str = None, **filters):
        """Obtains config value for the given key."""
        return Conf._conf.get(index, key, default_val, **filters)

    @staticmethod
    def delete(index: str, key: str, force: bool = False):
        """Deletes a given key from the config."""
        return Conf._conf.delete(index, key, force)

    @staticmethod
    def copy(src_index: str, dst_index: str, key_list: list = None,
        recurse: bool = True):
        """Creates a Copy suffixed file for main file."""
        Conf._conf.copy(src_index, dst_index, key_list, recurse)

    @staticmethod
    def merge(dest_index: str, src_index: str, keys: list = None):
        Conf._conf.merge(dest_index, src_index, keys)

    @staticmethod
    def compare(index1: str, index2: str):
        return Conf._conf.compare(index1, index2)

    class ClassProperty(property):
        """Subclass property for classmethod properties."""

        def __get__(self, cls, owner):
            return self.fget.__get__(None, owner)()

    @ClassProperty
    @classmethod
    def machine_id(self):
        """Returns the machine id from /etc/machine-id."""
        if Conf._conf is None:
            Conf.init()
        return self._machine_id.strip() if self._machine_id else None

    def get_keys(index: str, **filters) -> list:
        """
        Obtains list of keys stored in the specific config store.

        Input Paramters:
        Index   - Index for which the list of keys to be obtained
        Filters - Filters to be applied before the keys to be returned.
                  List of filters:
                  * key_index={True|False} (default: True)
                    when False, returns keys including array index
                    e.g. In case of "xxx[0],xxx[1]", only "xxx" is returned
        """
        return Conf._conf.get_keys(index, **filters)

    @staticmethod
    def search(index: str, parent_key: str, search_key: str,
        search_val: str = None) -> list:
        """
        Search for a given key or key-value under a parent key.

        Input Parameters:
        index   - Index for which the list of keys to be obtained
        parent_key - Parent Key under which the search would be conducted
        search_key - Key to be searched
        search_val - Value for the given search_key to be searched

        Returns list of keys that matched the creteria (i.e. has given value)
        """
        return Conf._conf.search(index, parent_key, search_key, search_val)

    @staticmethod
    def add_num_keys(index: str):
        """Add "num_xxx" keys for all the list items in ine KV Store."""
        Conf._conf.add_num_keys(index)

    @staticmethod
    def lock(index: str, **kwargs):
        """
        Attempt to acquire the config lock.
        :param index(required): Identifier of the config.
        :param domain(optional): Identity of the lock holder.
        :param owner(optional): Instance of domain sending lock request.
        :param duration(optional): Obtains the lock for the give duration in terms of seconds.

        :return: True if the lock was successfully acquired,
            false if it is already acquired by someone.
        """
        return Conf._conf.lock(index, **kwargs)

    @staticmethod
    def unlock(index: str, **kwargs):
        """
        Attempt to release the config lock.
        :param index(required): Identifier of the config.
        :param domain(optional): Identity of the Lock Holder.
        :param owner(optional): Instance of the domain sending unlock request.
        :param force(optional, default=False): When true, lock is forcefully released.

        :return: True if the lock was successfully released,
            false if it there is no lock or acquired by someone else unless force=true.
        """
        return Conf._conf.unlock(index, **kwargs)

    @staticmethod
    def test_lock(index: str, **kwargs):
        """
        Test whether Config is locked.
        :param index(required): param index: Identifier of the config.
        :param domain(optional): Identity of the Lock Holder.
        :param owner(optional): Instance of domain who needs to test lock.

        :return: True if lock can be acquired by someone else False
        """
        return Conf._conf.test_lock(index, **kwargs)

class MappedConf:
    """CORTX Config Store with fixed target."""

    _conf_idx = "cortx_conf"

    def __init__(self, conf_url):
        """Initialize with the CONF URL."""
        self._conf_url = conf_url
        Conf.load(self._conf_idx, self._conf_url, skip_reload=True)

    def set_kvs(self, kvs: list):
        """
        Set key:value.

        Parameters:
        kvs - List of KV tuple, e.g. [('k1','v1'),('k2','v2')]
        Where, k1, k2 - is full key path till the leaf key.
        """

        for key, val in kvs:
            try:
                Conf.set(self._conf_idx, key, val)
            except (AssertionError, ConfError) as e:
                raise ConfError(errno.EINVAL,
                    f'Error occurred while adding key {key} and value {val}'
                    f' in confstore. {e}')
        Conf.save(self._conf_idx)

    def set(self, key: str, val: str):
        """Save key-value in CORTX confstore."""
        try:
            Conf.set(self._conf_idx, key, val)
            Conf.save(self._conf_idx)
        except (AssertionError, ConfError) as e:
            raise ConfError(errno.EINVAL,
                f'Error occurred while adding key {key} and value {val}'
                f' in confstore. {e}')

    def copy(self, src_index: str, key_list: list = None):
        """Copy src_index config into CORTX confstore file."""
        try:
            Conf.copy(src_index, self._conf_idx, key_list)
        except (AssertionError, ConfError) as e:
            raise ConfError(errno.EINVAL,
                f'Error occurred while copying config into confstore. {e}')

    def search(self, parent_key: str, search_key: str, value: str = None):
        """Search for given key under parent key in CORTX confstore."""
        return Conf.search(self._conf_idx, parent_key, search_key, value)

    def add_num_keys(self):
        """Add "num_xxx" keys for all the list items in ine KV Store."""
        Conf.add_num_keys(self._conf_idx)

    def get(self, key: str, default_val: str = None) -> str:
        """Returns value for the given key."""
        return Conf.get(self._conf_idx, key, default_val)

    def delete(self, key: str, force: bool = False):
        """Delete key from CORTX confstore."""
        return Conf.delete(self._conf_idx, key, force)
