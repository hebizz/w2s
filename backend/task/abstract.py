import logging
import threading

from backend.settings import SYS_CONF


class AbstractTask(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.stopped = False
        self.succ_interval = SYS_CONF.get(self.name+"_interval", 30)
        self.fail_interval = SYS_CONF.get(self.name+"_failed_interval", 30)
        logging.info("task(%s): initiated", self.name)

    def run(self):
        raise NotImplementedError()

    def stop(self):
        self.stopped = True
