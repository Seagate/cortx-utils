import os
from cortx.utils import const
from cortx.utils.conf_store import Conf


class CortxConf:
    _index = 'config_file'

    @staticmethod
    def _load_config() -> None:
        """Load cortx.conf file into conf in-memory"""
        Conf.load(CortxConf._index, f'json://{const.CORTX_CONF_FILE}',
            skip_reload=True)

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
        CortxConf._load_config()
        log_dir = base_dir if base_dir else Conf.get(CortxConf._index, 'log_dir')
        return os.path.join(log_dir, f'cortx/utils/{Conf.machine_id}'\
            +f'{"/"+component if component else ""}')

    @staticmethod
    def get_key(key: str, default_val: str = None, **filters):
        """Obtain and return value for the given key"""
        CortxConf._load_config()
        return Conf.get(CortxConf._index, key, default_val, **filters)

    @staticmethod
    def set_key(key: str, value: str):
        """Sets the value into conf in-memory at the given key"""
        CortxConf._load_config()
        return Conf.set(CortxConf._index, key, value)

    @staticmethod
    def save():
        """Saves the configuration into the cortx.conf file"""
        Conf.save(CortxConf._index)
