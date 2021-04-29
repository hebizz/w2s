import time
import logging
import threading
from schedule import Scheduler

from backend.driver import bucket as bktctl
from backend.driver import camera as camctl
from backend.driver import recogn as rcgctl
from backend.driver import clock as clkctl
from backend.driver import poseidon as podctl
from backend.driver.mongo import mongodb
from backend.settings import SYS_CONF
from backend.task.abstract import AbstractTask
from backend.model import device


class RoutineTask(AbstractTask):
    def __init__(self):
        super().__init__("routine")
        self.cap_th = {}

    def run(self):
        if device.is_edge_ipc() and not mongodb.device.find_one({"cam_type" : "TD201"}):
            camctl.add("TD201", None, None, None, cam_uuid=podctl.get_poseidon_id())
        while not self.stopped:
            try:
                self.__run()
            except Exception as err:
                logging.exception(err)
                logging.info("task(%s): fail and next in: %s", self.name, self.fail_interval)
                time.sleep(self.fail_interval)

    def __run(self):
        camera_list = camctl.get_all({})[0]
        logging.info("found %s camera(s) in database", len(camera_list))
        for cam in camera_list:
            if cam.uuid not in self.cap_th or self.cap_th[cam.uuid].stopped:
                self.cap_th[cam.uuid] = CapSaveRecognTask(cam.uuid)
                self.cap_th[cam.uuid].start()
        logging.info("task(%s): succ and next in: %s", self.name, self.succ_interval)
        time.sleep(self.succ_interval)

    def insert_subtask(self, uuid):
        self.cap_th[uuid] = CapSaveRecognTask(uuid)
        self.cap_th[uuid].start()

    def remove_subtask(self, uuid):
        cam = camctl.get_one(uuid)
        try:
            if uuid in self.cap_th:
                self.cap_th[uuid].stop()
                del self.cap_th[uuid]
        except Exception as err:
            logging.exception(err)
            logging.info("subtask(%s): failed to stop", cam.name)

class CapSaveRecognTask(AbstractTask):
    def __init__(self, uuid):
        super().__init__("capcam")
        self.cam_uuid = uuid
        self.success_interval = camctl.get_one(self.cam_uuid).interval
        self.schedule = Scheduler()

    def run(self):
        self.schedule.clear()
        self.schedule.every(self.success_interval).seconds.do(self.run_threaded, self.__run)
        while not self.stopped:
            try:
                self.schedule.run_pending()
                time.sleep(1)
            except Exception as err:
                logging.error("task(%s@%s) failed, %s", self.name, self.cam_uuid, str(err))
                time.sleep(self.fail_interval)

    def __run(self):
        try:
            cam = camctl.get_one(self.cam_uuid)
            if clkctl.check_period_filter(cam.detection_cycle.get('detection_period'), cam.detection_cycle.get('detection_time')):
                if_sto_img = camctl.if_sto_img(cam)
                saved_path, if_sto_db = bktctl.save(cam.frame(), self.cam_uuid, if_sto_img)
                function_list = rcgctl.period_function_filter(cam)
                model_list = rcgctl.ai_pointer_filter(function_list)
                logging.info(model_list)

                if len(model_list):
                    logging.info("task(%s@%s): start ai recognize, function is : %s, model is : %s", self.name, self.cam_uuid, str(function_list), str(model_list))
                    rcgctl.recognize(saved_path, self.cam_uuid, function_list, model_list)
                    logging.info("task(%s@%s): succ and next in: %s", self.name, self.cam_uuid, cam.interval)
                else:
                    logging.info("task(%s@%s): not in ai recognize cycle", self.name, self.cam_uuid)

                if not if_sto_db:
                    bktctl.delete(saved_path)
            if cam.interval != self.success_interval:
                self.success_interval = cam.interval
                self.schedule.clear()
                self.schedule.every(self.success_interval).seconds.do(self.run_threaded, self.__run)
        except Exception as err:
            logging.error("task(%s) failed", self.name)
            logging.exception(err)
            logging.info("task(%s@%s): fail and next in: %s", self.name, self.cam_uuid, self.fail_interval)
            self.success_interval = self.fail_interval
            self.schedule.clear()
            self.schedule.every(self.fail_interval).seconds.do(self.run_threaded, self.__run)

    def run_threaded(self, func):
        job_thread = threading.Thread(target=func)
        job_thread.start()
