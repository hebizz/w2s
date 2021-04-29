import os
import time
import logging
import datetime
import threading

from backend.settings import SYS_CONF
from backend.driver import bucket as bktctl
from backend.task.abstract import AbstractTask


class Sweeper(AbstractTask):
    def __init__(self):
        super().__init__("sweeper")
        self.clean_quota = SYS_CONF.get("sweep_by_quota", 80)

    def run(self):
        while not self.stopped:
            try:
                bktctl.clean_by_date()
                bktctl.clean_by_quota(self.clean_quota)
                logging.info("task(%s): succ and next in: %s", self.name, self.succ_interval)
                time.sleep(self.succ_interval)
            except Exception as err:
                logging.error("task(%s) failed", self.name)
                logging.exception(err)
                logging.info("task(%s): fail and next in: %s", self.name, self.fail_interval)
                time.sleep(self.fail_interval)
