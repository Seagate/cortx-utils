import os
from cortx.utils import const
from cortx.utils.conf_store import Conf


class CortxConf():

    def __init__(self) -> None:
        Conf.load('config_file', f'json://{const.CORTX_CONF_FILE}',
            skip_reload=True)
        self.machine_id = Conf.machine_id

    def get_log_path(self, component = None, base_dir: str = None) -> str:
        log_dir = base_dir if base_dir else Conf.get('config_file', 'log_dir')
        return os.path.join(log_dir, f'cortx/utils/{self.machine_id}'\
            +f'{"/"+component if component else ""}')

    def get_key(self, key: str, default_val: str = None, **filters):
        return Conf.get('config_file', key, default_val, **filters)

    def set_key(self, key: str, value: str):
        return Conf.set('config_file', key, value)

    def save(self):
        return Conf.save('config_file')
