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
            raise ConfError(errno.ENOENT, "Invalid value for recurse %s", val)
        return CortxConf._cluster_conf
