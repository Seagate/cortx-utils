import os
import errno
from pathlib import Path
from urllib.parse import urlparse

from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError


class CortxConf:
    _index = 'config_file'

    @staticmethod
    def _load_config(cluster_conf: str) -> None:
        """Load cortx.conf file into conf in-memory."""
        local_storage_path = CortxConf.get_storage_path('local', cluster_conf)
        Conf.load(CortxConf._index, \
            f"json://{os.path.join(local_storage_path, 'utils/conf/cortx.conf')}", \
            skip_reload=True)

    @staticmethod
    def get_storage_path(key: str, cluster_conf: str) -> str:
        """Get the config file path."""
        url_spec = urlparse(cluster_conf)
        store_type = url_spec.scheme
        store_loc = url_spec.netloc
        store_path = url_spec.path
        cluster_path = Path(store_path)
        if not cluster_path.is_file():
            raise UtilsError(errno.ENOENT, "Invalid cluster.conf file path")
        Conf.load('cluster', cluster_conf, skip_reload=True)
        path = Conf.get('cluster', f'cortx>common>storage>{key}')
        if not path:
            raise ConfError(errno.EINVAL, "Invalid key %s", key)
        return path

    @staticmethod
    def get_log_path(component = None, base_dir: str = None, cluster_conf: str = None) -> str:
        """
        Get the log path with machine-id as sub directory

        Parameters:
        Component: Name of the component directory. If passed then the
                   method will return component directory as sub directory
                   of machine-id. ex arguments. message_bus/ iem
                   Default = None
        base_dir: root directory where all the log sub-directories should be create.
        """
        CortxConf._load_config(cluster_conf)
        log_dir = base_dir if base_dir else Conf.get(CortxConf._index, 'log_dir')
        return os.path.join(log_dir, f'utils/{Conf.machine_id}'\
            +f'{"/"+component if component else ""}')

    @staticmethod
    def get(key: str, default_val: str = None, cluster_conf: str = None, **filters):
        """Obtain and return value for the given key."""
        CortxConf._load_config(cluster_conf)
        return Conf.get(CortxConf._index, key, default_val, **filters)

    @staticmethod
    def set(key: str, value: str, cluster_conf:str = None):
        """Sets the value into conf in-memory at the given key."""
        CortxConf._load_config(cluster_conf)
        return Conf.set(CortxConf._index, key, value)

    @staticmethod
    def save():
        """Saves the configuration into the cortx.conf file."""
        Conf.save(CortxConf._index)
