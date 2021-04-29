import copy
import logging

import numpy as np

from backend.driver import clock
from backend.driver import function as functl
from backend.driver import camera as camctl
from backend.driver import face as factl
from backend.misc.utils import _isInsidePolygon, reslove_result, threshold_filter

class Warning_Parser(object):
    def __init__(self, parse_list):
        self.parse_list = parse_list

    def __call__(self, raw_results, cam):
        logging.info("ai_raw_results: {}".format(raw_results))
        ai_result = {}
        for f in self.parse_list:
            func_results = f(raw_results, cam)
            ai_result.update(func_results)
        logging.info("ai_parse_results: {}".format(ai_result))
        threshold_result = threshold_filter(ai_result, cam)
        logging.info("threshold_parse_results: {}".format(threshold_result))
        return threshold_result

class fire_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # fire filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'huoyan':
                        filter_results.append(result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "huoyan":
                        min_point = {'x': int(result[2]), 'y': int(result[3])}
                        max_point = {'x': int(result[4]), 'y': int(result[5])}
                        for zone in cam_zones:
                            is_min_inside = _isInsidePolygon(min_point, zone)
                            is_max_inside = _isInsidePolygon(max_point, zone)
                            if is_min_inside or is_max_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results

class restrict_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # fire filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'person_body':
                        filter_results.append(result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "person_body":
                        left_leg_x = int(result[2])
                        right_leg_x = int(result[4])
                        leg_y = int(result[5])
                        check_point = {"x": int((left_leg_x + right_leg_x)/2), "y": leg_y}
                        for zone in cam_zones:
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results

class no_helmet_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # no_helmet filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'person':
                        filter_results.append(result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "person":
                        left_leg_x = int(result[2])
                        right_leg_x = int(result[4])
                        leg_y = int(result[5])
                        check_point = {"x": int((left_leg_x + right_leg_x)/2), "y": leg_y}
                        for zone in cam_zones:
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results

class smoke_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # mask filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'yanhuo':
                        filter_results.append(result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "yanhuo":
                        left_leg_x = int(result[2])
                        right_leg_x = int(result[4])
                        leg_y = int(result[5])
                        check_point = {"x": int((left_leg_x + right_leg_x)/2), "y": leg_y}
                        for zone in cam_zones:
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results

class pata_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # fire filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'person':
                        result_temp = copy.deepcopy(result)
                        result_temp[0] = "pata"
                        result_temp[2] = str(int(result_temp[2]) - 15)
                        result_temp[4] = str(int(result_temp[4]) + 15)
                        result_temp[5] = str(3 * (int(result_temp[5]) - int(result_temp[3])) + int(result_temp[5]))
                        filter_results.append(result_temp)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "person":
                        result_temp = copy.deepcopy(result)
                        result_temp[0] = "pata"
                        result_temp[2] = str(int(result_temp[2]) - 15)
                        result_temp[4] = str(int(result_temp[4]) + 15)
                        result_temp[5] = str(3 * (int(result_temp[5]) - int(result_temp[3])) + int(result_temp[5]))
                        left_down_x = int(result[2])
                        right_down_x = int(result[4])
                        down_y = int(result[5])
                        check_point = {"x": int((left_down_x + right_down_x)/2), "y": down_y}
                        for zone in cam_zones:
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result_temp)
                        else:
                            if in_flag:
                                filter_results.append(result_temp)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results

class machinery_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # mask filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'shigongjixie':
                        filter_results.append(result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "shigongjixie":
                        left_leg_x = int(result[2])
                        right_leg_x = int(result[4])
                        leg_y = int(result[5])
                        check_point = {"x": int((left_leg_x + right_leg_x)/2), "y": leg_y}
                        for zone in cam_zones:
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results

class move_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # mask filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                for result in raw_results:
                    if result[0] == 'movement':
                        filter_results.append(result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                for result in raw_results:
                    in_flag = False
                    if result[0] == "movement":
                        left_leg_x = int(result[2])
                        right_leg_x = int(result[4])
                        leg_y = int(result[5])
                        check_point = {"x": int((left_leg_x + right_leg_x)/2), "y": leg_y}
                        for zone in cam_zones:
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results


class leave_filter(object):
    def __init__(self, func_name):
        self.func_name = func_name

    def __call__(self, raw_results, cam):
        # leave filter
        cam_function = cam.function
        cam_info = cam_function.get(self.func_name, {})
        cam_reverse = cam_info.get("reverse", False)
        aggreagate_time = functl.get(self.func_name).get("aggreagate", 300)
        filter_results = []
        if cam_info.get("enable", False):
            logging.info("_apply_{}_filter:: filtering...".format(self.func_name))
            cam_zones = cam_info.get("zones", [])
            cam_detected_times = cam.detected_times
            _, _, ts = clock.now()
            if cam_zones == []:
                logging.info("apply_{}_filter:: zones: whole img".format(self.func_name))
                logging.info("last detected time is:: {}, current time is:: {}".format(clock._get_csttz_dt(cam_detected_times[0]), clock._get_csttz_dt(ts)))
                detected_flag = False
                for result in raw_results:
                    if result[0] == 'person_body':
                        detected_flag = True
                if detected_flag:
                    cam_detected_times = [ts]
                    camctl.update(cam.uuid, {"detected_times": cam_detected_times})
                else:
                    if (ts - cam_detected_times[0]) > aggreagate_time:
                        return_result = ["leave", 0.666, "0", "0", "1", "1"]
                        filter_results.append(return_result)
            else:
                logging.info("_apply_{}_filter:: zones: {}".format(self.func_name, cam_zones))
                if len(cam_detected_times) != len(cam_zones):
                    cam_detected_times = [ts] * len(cam_zones)

                for result in raw_results:
                    in_flag = False
                    in_index = -1
                    if result[0] == "person_body":
                        left_leg_x = int(result[2])
                        right_leg_x = int(result[4])
                        leg_y = int(result[5])
                        check_point = {"x": int((left_leg_x + right_leg_x)/2), "y": leg_y}
                        for i, zone in enumerate(cam_zones):
                            check_point_inside = _isInsidePolygon(check_point, zone)
                            if check_point_inside:
                                in_flag = True
                                in_index = i
                        if in_flag:
                            cam_detected_times[in_index] = ts
                camctl.update(cam.uuid, {"detected_times": cam_detected_times})
                for i, zone in enumerate(cam_zones):
                    detected_time = cam_detected_times[i]
                    logging.info("zone {} @ last detected time is:: {}, current time is:: {}".format(i, clock._get_csttz_dt(detected_time), clock._get_csttz_dt(ts)))
                    if (ts - detected_time) > aggreagate_time:
                        xmin = str(zone[0]["x"])
                        ymin = str(zone[0]["y"])
                        xmax = str(zone[2]["x"])
                        ymax = str(zone[2]["y"])
                        return_result = ["leave", 0.666, xmin, ymin, xmax, ymax]
                        filter_results.append(return_result)
                        """
                        if cam_reverse:
                            if not in_flag:
                                filter_results.append(result)
                        else:
                            if in_flag:
                                filter_results.append(result)
                        """

        logging.info("_apply_{}_filter:: results: {}".format(self.func_name, filter_results))
        parse_results = reslove_result(filter_results, self.func_name)
        return parse_results
