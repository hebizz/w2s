import logging
import time
import yaml

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.settings import SYS_CONF
from backend.task.abstract import AbstractTask

path = SYS_CONF["poseidon_file_path"]


class WatchEventHandler(FileSystemEventHandler):

    def on_created(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        self.init_web_conf_by_yaml()

    @staticmethod
    def init_web_conf_by_yaml():
        try:
            # 加载poseidon.yaml文件
            with open(path) as f:
                temp = yaml.load(f.read())
            SYS_CONF['host_ip'] = temp['host_ip']
            SYS_CONF['chip_pointer'] = temp['chip_pointer']
            logging.info(SYS_CONF['host_ip'])
            logging.info(SYS_CONF['chip_pointer'])
        except Exception as e:
            logging.error("init web config failed :{}".format(str(e)))


class PoseidonConfig(AbstractTask):
    def __init__(self):
        super().__init__("webconfig")

    def run(self):
        self.watch_poseidon_file()

    @staticmethod
    def watch_poseidon_file():
        event_handler = WatchEventHandler()
        event_handler.init_web_conf_by_yaml()
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
