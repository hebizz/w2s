import os
import logging

from backend.driver import clock
from backend.handlers import base
from backend.driver import camera as camctl
from backend.driver import bucket as bktctl
from backend.driver import function as functl
from backend.driver import memory


class FunctionHandler(base.AsyncHandler):
    def do_get(self, data):
        return self.success(functl.get(""))

    def do_put(self, data):
        return self.success(functl.update_all(data))

class CameraSetHandler(base.AsyncHandler):
    def do_get(self, data):
        """ list function setting of a specific camera or all cameras """
        device_id = data.get("device_id")
        try:
            cameras = []
            if device_id is None:
                cameras = camctl.get_all({})[0]
            else:
                cameras = [camctl.get_one(device_id)]
            data = [{
                "device_id": c.uuid,
                "function": c.function,
                "frame": os.path.join(
                  "/media/{}/image".format(c.uuid),
                  bktctl.latest_images(c.uuid, 1)[0]['name'])
            } for c in cameras]
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))
        return self.success(data)

    def do_put(self, data):
        """ overwrite all function settings of a specific camera """
        device_id = data.get("device_id")
        new_setting = data.get("function")
        try:
            if not isinstance(new_setting, dict):
                raise RuntimeError("invalid parameters")
            camctl.update(device_id, {"function": new_setting})
            cam = camctl.get_one(device_id)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))
        return self.success(cam.function)

    def do_post(self, data):
        """ modify part of function settings of a specific camera """
        device_id = data.get("device_id")
        func_name = data.get("func_name")
        enable = data.get("enable", False)
        zones = data.get("zones", [[]])
        reverse = data.get("reverse", False)
        threshold = data.get("threshold", 0.2)
        detection_cycle = data.get("detection_cycle",
                                   {
                                       "detection_starttime": 0,
                                       "detection_endtime": 64800,
                                       "detection_period": [0,1,2,3,4,5,6],
                                   })
        _, _, ts = clock.now()
        detected_time = [ts] * len(zones)

        try:
            cam = camctl.get_one(device_id)
            if func_name not in functl.get(""):
                raise RuntimeError("invalid function id")
            if not isinstance(zones, list):
                raise RuntimeError("invalid parameters")

            all_function = cam.function
            function_spec = all_function.get(func_name, {})
            function_spec["enable"] = enable
            function_spec["zone"] = zones
            function_spec["reverse"] = reverse
            function_spec["threshold"] = threshold
            function_spec["detection_cycle"] = detection_cycle
            function_spec["detected_time"] = detected_time
            all_function[func_name] = function_spec
            camctl.update(device_id, {"function": all_function})
            cam = camctl.get_one(device_id)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))
        return self.success(cam.function)
