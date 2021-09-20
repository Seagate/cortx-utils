import os
from cortx.utils import const
from cortx.utils.conf_store import Conf


class CortxConf():

    def load_config() -> None:
        Conf.load('config_file', f'json://{const.CORTX_CONF_FILE}',
            skip_reload=True)

    @staticmethod
    def get_log_path(component = None, base_dir: str = None) -> str:
        CortxConf.load_config()
        log_dir = base_dir if base_dir else Conf.get('config_file', 'log_dir')
        return os.path.join(log_dir, f'cortx/utils/{Conf.machine_id}'\
            +f'{"/"+component if component else ""}')

    @staticmethod
    def get_key(key: str, default_val: str = None, **filters):
        CortxConf.load_config()
        return Conf.get('config_file', key, default_val, **filters)

    @staticmethod
    def set_key(key: str, value: str):
        CortxConf.load_config()
        return Conf.set('config_file', key, value)

    @staticmethod
    def save():
        return Conf.save('config_file')
