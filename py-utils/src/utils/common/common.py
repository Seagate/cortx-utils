import os
import errno

from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError


class CortxConf:
    _index = 'config_file'
    _cluster_index = 'cluster'
    _cluster_conf = None

    @staticmethod
    def init(**kwargs):
        """
        static init for initialising
        Arguments:
        cluster_conf:
            confStore path of cluster.conf. eg. yaml:///etc/cortx/cluster.conf
        """
        for key, val in kwargs.items():
            setattr(CortxConf, f'_{key}', val)
        CortxConf._load_cluster_conf()
        CortxConf._load_config()

    @staticmethod
    def _load_config() -> None:
        """Load cortx.conf file into conf in-memory."""
        local_storage_path = CortxConf.get_storage_path('local')
        Conf.load(CortxConf._index, \
            f"json://{os.path.join(local_storage_path, 'utils/conf/cortx.conf')}", \
            fail_reload=False)

    @staticmethod
    def _load_cluster_conf():
        Conf.load(CortxConf._cluster_index, CortxConf._cluster_conf,\
            fail_reload=False)

    @staticmethod
    def get_storage_path(key):
        """Get the config file path."""
        path = Conf.get(CortxConf._cluster_index, f'cortx>common>storage>{key}')
        if not path:
            raise ConfError(errno.EINVAL, "Invalid key %s", key)
        return path

    @staticmethod
    def get_log_path(component = None, base_dir: str = None) -> str:
        """
        Get the log path with machine-id as sub directory

        Parameters:
        Component: Name of the component directory. If passed then the
                   method will return component directory as sub directory
                   of machine-id. ex arguments. message_bus/ iem
                   Default = None
        base_dir: root directory where all the log sub-directories should be create.
        """
        log_dir = base_dir if base_dir else Conf.get(CortxConf._index, 'log_dir')
        return os.path.join(log_dir, f'utils/{Conf.machine_id}'\
            +f'{"/"+component if component else ""}')

    @staticmethod
    def get(key: str, default_val: str = None, **filters):
        """Obtain and return value for the given key."""
        return Conf.get(CortxConf._index, key, default_val, **filters)

    @staticmethod
    def set(key: str, value: str):
        """Sets the value into conf in-memory at the given key."""
        return Conf.set(CortxConf._index, key, value)

    @staticmethod
    def save():
        """Saves the configuration into the cortx.conf file."""
        Conf.save(CortxConf._index)

    @staticmethod
    def get_cluster_conf_path():
        if CortxConf._cluster_conf is None:
            raise ConfError(errno.ENOENT, "Path for config file, cluster.conf, not provided")
        return CortxConf._cluster_conf


class ConfigStore:

    """ CORTX Config Store """

    _conf_idx = "cortx_conf"

    def __init__(self, conf_url):
        """ Initialize with the CONF URL."""
        self._conf_url = conf_url
        Conf.load(self._conf_idx, self._conf_url, skip_reload=True)

    def set_kvs(self, kvs: list):
        """
        Parameters:
        kvs - List of KV tuple, e.g. [('k1','v1'),('k2','v2')]
        """

        for key, val in kvs:
            Conf.set(self._conf_idx, key, val)
        Conf.save(self._conf_idx)

    def set(self, key: str, val: str):
        """Sets the value into conf in-memory at the given key."""
        Conf.set(self._conf_idx, key, val)
        Conf.save(self._conf_idx)

    def get(self, key: str) -> str:
        """ Returns value for the given key """

        return Conf.get(self._conf_idx, key)
