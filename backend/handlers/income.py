import os
import logging

from backend.handlers import base
from backend.driver import camera as camctl
from backend.driver import bucket as bktctl
from backend.driver import recogn as rcgctl
from backend.driver import function as functl


class IncomeHandler(base.AsyncHandler):
    def do_post(self, data):
        """ income alert """
        device_id = camctl._gen_id("10.48.48.10")
        rcg_result = data.get("result")
        rcg_images = data.get("images")
        try:
            cam = camctl.get_one(device_id)
            saved_path, _ = bktctl.save(rcg_images, cam.uuid)
            function_list = rcgctl.period_function_filter(cam)
            model_list = rcgctl.ai_pointer_filter(function_list)
            # rcgctl.recognize(saved_path, device_id, function_list, model_list, overwrite=rcg_result)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))
        return self.success(cam.function)
