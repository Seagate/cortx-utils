from multiprocessing import Process
import random
from datetime import datetime
import string
from time import sleep
from cortx.utils.conf_store import Conf

class TestConfStoreLock(object):
    """Test Confstore lock."""
    lock_status = []
    def __init__(self, URL="consul://cortx-consul-server:8500/test_lock"):
        self.url = URL
        self.duration = 20

    def test_lock_race(self, thread_count:int = 2, repeat = 1):
        """Test race condition with lock."""
        _index = None
        _conf_index = TestConfStoreLock._generate_index()
        _process_store = []
        for num in range(0, thread_count):
            _index = _conf_index + str(num)
            Conf.load(_index, self.url)
            _conf_process = Process(target=self.do_lock, args=(_index, repeat, 2), kwargs={ "owner": _index, "duration":self.duration})
            _process_store.append(_conf_process)

        for _proc in _process_store:
            _proc.start()

    def test_multiple_lock_unlock(self, thread_count:int = 2, repeat = 1):
        """Test race condition with lock."""
        _index = None
        _conf_index = TestConfStoreLock._generate_index()
        _process_store = []
        for num in range(0, thread_count):
            _index = _conf_index + str(num)
            Conf.load(_index, self.url)
            _conf_process = Process(target=self.lock_unlock, args=(_index, repeat), kwargs={ "owner": _index, "duration":self.duration})
            _process_store.append(_conf_process)

        for _proc in _process_store:
            _proc.start()
            _proc.join()

    def test_multiple_lock_reset_lock(self, thread_count:int = 2, repeat = 1):
        """Test race condition with lock."""
        _index = None
        _conf_index = TestConfStoreLock._generate_index()
        _process_store = []
        for num in range(0, thread_count):
            _index = _conf_index + str(num)
            Conf.load(_index, self.url)
            _conf_process = Process(target=self.lock_reset_lock, args=(_index, repeat), kwargs={ "owner": _index })
            _process_store.append(_conf_process)

        for _proc in _process_store:
            _proc.start()
            _proc.join()

    def test_multiple_lock_and_test_lock(self, thread_count = 2, repeat=1):
        """Test race condition with lock."""
        _index = None
        _conf_index = TestConfStoreLock._generate_index()
        _process_store = []
        for num in range(0, thread_count):
            _index = _conf_index + str(num)
            Conf.load(_index, self.url)
            _conf_process = Process(target=self.lock_and_test_lock, args=(_index, repeat), kwargs={ "owner": _index, "duration":self.duration })
            _process_store.append(_conf_process)

        for _proc in _process_store:
            _proc.start()
            _proc.join()

    def test_process_lock_recover(self, thread_count = 2, repeat=1):
        """Test race condition with lock."""
        _index = None
        first_index = None
        _conf_index = TestConfStoreLock._generate_index()
        _process_store = []
        for num in range(0, thread_count):
            _index = _conf_index + str(num)
            Conf.load(_index, self.url)
            if first_index is None:
                first_index = _index
                _conf_process = Process(target=self.do_lock, args=(_index, 1, 2), kwargs={ "owner": _index , "duration":self.duration})
                _conf_process.start()
                sleep(20)
                print(f"process terminated {first_index}")
                _conf_process.terminate()
                continue

            _conf_process = Process(target=self.do_lock, args=(_index, repeat, 5), kwargs={ "owner": _index, "duration":self.duration})
            _process_store.append(_conf_process)

        for _proc in _process_store:
            _proc.start()
            _proc.join()
        sleep(10)
        print(f"Process started again {first_index}")
        _conf_process = Process(target=self.do_lock, args=(first_index, 1, 2), kwargs={ "owner": first_index, "duration":self.duration})
        _conf_process.start()

    def lock_unlock(self, index, repeat, **kwargs):
        for rep in range(0, repeat):
            print(f"Rep {index} {rep+1}")
            self.do_lock(index, 1, **kwargs)
            sleep(1)
            self.do_unlock(index, 1)

    def lock_reset_lock(self, index, repeat, **kwargs):
        for rep in range(0, repeat):
            print(f"Rep {index} {rep+1}")
            self.do_lock(index, 1, **kwargs)
            sleep(1)
            self._reset_lock(index)

    def lock_and_test_lock(self, index, repeat, **kwargs):
        for rep in range(0, repeat):
            print(f"Rep {index} {rep+1}")
            self.do_lock(index, 1, **kwargs)
            sleep(1)
            self._test_lock(index, 1)
            self.do_unlock(index,1)
            sleep(1)
            self._test_lock(index, 1)

    def _test_lock(self, index, repeat):
        for rep in range(0, repeat):
            print(f"Test Lock Rep {index} {rep+1}")
            print(f"{datetime.now()} Test Lock Status for {index}: {Conf.test_lock(index, owner=index)}")

    def do_lock(self, index, repeat = 1, sleep_time = 0, **kwargs):
        """lock config."""
        for rep in range(0, repeat):
            print(f"Lock Rep {index} {rep+1}")
            status = Conf.lock(index, **kwargs)
            if status and index not in TestConfStoreLock.lock_status:
                TestConfStoreLock.lock_status.append(index)
                if len(TestConfStoreLock.lock_status) > 1:
                    print("Error: More than 2 process have acquired the lock")
                    print(TestConfStoreLock.lock_status)
                    exit()
            print(f"{datetime.now()} Lock Status for {index}: {status} ")
            sleep(sleep_time)

    def do_unlock(self, index, repeat=1):
        """Unlock config."""
        for rep in range(0, repeat):
            print(f"Unlock Rep {index} {rep+1}")
            status = Conf.unlock(index, owner=index)
            if status:
                TestConfStoreLock.lock_status.remove(index)
            print(f"{datetime.now()} UnLock Status for {index}: {status} ")

    def _reset_lock(self, _index = None):
        """Reset lock status."""
        if _index is None:
            _index = self._generate_index()
            Conf.load(_index, self.url)
        status = Conf.unlock(_index, force=True)
        if status and _index in TestConfStoreLock.lock_status:
            TestConfStoreLock.lock_status.remove(_index)
        print(f"{datetime.now()} Reset status: {status}")

    @staticmethod
    def _generate_index():
        """Generate random index."""
        digits = random.choices(string.digits, k=2)
        letters = random.choices(string.ascii_uppercase, k=9)
        return ''.join(random.sample(digits + letters, 11))


if __name__ == '__main__':
    run_count = int(input("Run Count: "))
    thread_count = int(input("Thread count: "))
    rep = int(input("Repeat: "))
    _test_lock = TestConfStoreLock()
    _test_lock._reset_lock()
    for run in range(0, run_count):
        print(f"Run: {run+1}")
        # from below Call only one function at a time for testing
        # different test scenarios
        _test_lock.test_lock_race(thread_count, rep)
        # _test_lock.test_multiple_lock_unlock(thread_count, rep)
        # _test_lock.test_multiple_lock_reset_lock(thread_count, rep)
        # # _test_lock.test_multiple_lock_and_test_lock(thread_count, rep)
        # _test_lock.test_process_lock_recover(thread_count, rep)
