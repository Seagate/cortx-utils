from cortx.utils.validator.v_service import ServiceV
from cortx.utils.process import SimpleProcess
import time

class RsyslogService:
    """
    Class to handle rsyslog service restart
    """
    @staticmethod
    def _validate_service():
        ServiceV().validate('isrunning', ["rsyslog"])

    @staticmethod
    def restart_rsyslog():
        cmd = "systemctl restart rsyslog.service"
        _proc = SimpleProcess(cmd)
        for count in range(0, 10):
            try:
                _proc.run(universal_newlines=True)
                RsyslogService._validate_service()
                break
            except Exception:
                time.sleep(2**count)
