import time
import logging
import base64
import copy
import os
import shutil

from backend.settings import SYS_CONF
from backend.model.alert import Alert
from backend.driver import clock
from backend.driver import function as functl
from backend.driver.mongo import mongodb, resize_mongo_result, mongo_id_to_str
from backend.driver import memory
from backend.middle import Middle

IMG_BASE_PATH = "/var/w2s"


def get_all(query, limit=0, offset=0):
    """查询报警"""
    fetch = mongodb.alerts.find(query, sort=[('status', -1), ('create_time', -1)])
    results = resize_mongo_result(fetch, limit=limit, offset=offset)
    return [Alert(mongo_id_to_str(it)) for it in results], fetch.count()


def confirm(query, user_name, user_id):
    """确认报警"""
    mongodb.alerts.update_one(query, {'$set': {
        "affirmed": True,
        "affirm_time": int(time.time()),
        "affirm": user_name,
        "affirm_id": user_id
    }})
    result = mongo_id_to_str(mongodb.alerts.find_one(query))
    return Alert(result)


def close(query, user_name, user_id):
    """关闭报警"""
    mongodb.alerts.update_many(query, {'$set': {
        "status": "closed",
        "operator_time": int(time.time()),
        "operator": user_name,
        "operator_id": user_id
    }})
    results = mongodb.alerts.find(query)
    alerts = []
    if results:
        for result in results:
            data = mongo_id_to_str(result)
            alerts.append(Alert(data))
    return alerts


def delete(query):
    mongodb.alerts.delete_many(query)


def summary(query):
    results = mongodb.alerts.find(query)

    current_devices = mongodb.device.find()
    current_device_ids = []
    for device in current_devices:
        if device.get("uuid"):
            current_device_ids.append(device.get("uuid"))

    alerts = []
    alerts_device = set([])
    opening_alerts = []
    for result in results:
        alerts.append(result)
        if result.get("status") == "opening":
            if result.get("device_id") in current_device_ids:
                alerts_device.add(result.get("device_id"))
            opening_alerts.append(result)
    return len(alerts), len(opening_alerts), len(alerts_device)


def summary_status(query):
    """ 查询开和关的报警数量 """
    results = mongodb.alerts.find(query)
    close_alerts = []
    opening_alerts = []
    for result in results:
        if result.get("status") == "opening":
            opening_alerts.append(result)
        else:
            close_alerts.append(result)

    return len(close_alerts), len(opening_alerts)


def summary_category(query):
    """ 查询各种类型报警数量 """
    results = mongodb.alerts.find(query)

    alert_sum_dict = {}
    all_functions = functl.get("")

    # all_alert_type = SYS_CONF.get("all_alerts", [])

    for func_name in all_functions:
        alert_sum_dict[func_name] = 0
    for result in results:
        title = result.get("func_name")
        if title in alert_sum_dict:
            alert_sum_dict[title] += 1

    return alert_sum_dict


def allowed_alert_type():
    status = functl.get("")
    allowed_alert = []
    allowed_title = []
    for k, v in status.items():
        if v.get("enable", False):
            allowed_alert.append(k)
            allowed_title.append(v.get("title", ""))
    return allowed_alert, allowed_title


def create(cam, func_name, result_info, image_path):
    alert_allowed, _ = allowed_alert_type()

    if func_name not in alert_allowed:
        logging.info("alert(%s) raise, but will not prompt", func_name)
        return False

    _, _, ts = clock.now()

    alert = {
        "sub_type": "camera",
        "device_id": cam.uuid,
        "device_name": cam.name,
        "host_id": SYS_CONF.get("host_id"),
        "host_ip": SYS_CONF.get("host_ip"),
        "func_name": func_name,
        "title": functl.get(func_name).get("title", ""),
        # TODO: alert_position should be renamed
        "alert_position": result_info,
        "create_time": ts,
        "location": cam.location,
        "status": "opening",
        "affirmed": False,
        "level": cam.function.get(func_name, {}).get("alert_level", functl.get(func_name).get("alert_level", "")),
    }

    aggreagate = cam.function[func_name].get("aggreagate", 60)
    warning_count = memory.WARNING_COUNT[cam.uuid].get(func_name, [])
    logging.info("driver.alert:: warning_count of func@{} is {}".format(func_name, warning_count))
    aggreagate_times = cam.function[func_name].get("aggreagate_times", 1)

    # aggreagate_times=1, 超过告警间隔才发送告警
    if aggreagate_times == 1:
        result = mongodb.alerts.find_one(
            {"create_time": {'$gte': (ts - aggreagate)},
             "device_id": cam.uuid, "func_name": func_name})
        if result:
            return False
        _save_alert_in_db(alert, image_path, cam)
        alert_data = copy.deepcopy(alert)
        alert_data.pop("_id", None)
        alert_data["create_time"] = ts * 1000
        Middle.CldT.report_alert(alert_data, cam, os.path.join(IMG_BASE_PATH, image_path))
        return True

    # aggreagate_times>1，aggreagate内连续告警超过aggreagate_tims才告警
    if len(warning_count) < aggreagate_times:
        memory.WARNING_COUNT[cam.uuid][func_name].append(ts)
        if len(memory.WARNING_COUNT[cam.uuid][func_name]) == aggreagate_times:
            if (ts - warning_count[0]) <= aggreagate:
                memory.WARNING_COUNT[cam.uuid][func_name].pop(0)
                result = mongodb.alerts.find_one(
                    {"create_time": {'$gte': (ts - aggreagate + 1)},
                     "device_id": cam.uuid, "func_name": func_name})
                if result:
                    return False
                _save_alert_in_db(alert, image_path, cam)
                alert_data = copy.deepcopy(alert)
                alert_data.pop("_id", None)
                alert_data["create_time"] = ts * 1000
                Middle.CldT.report_alert(alert_data, cam, os.path.join(IMG_BASE_PATH, image_path))
                return True
        return False

    # 当aggreagate_times改小时，只截取一部分ts
    if len(warning_count) >= aggreagate_times:
        memory.WARNING_COUNT[cam.uuid][func_name].append(ts)
        memory.WARNING_COUNT[cam.uuid][func_name] = memory.WARNING_COUNT[cam.uuid][func_name][-aggreagate_times:]
        if (ts - memory.WARNING_COUNT[cam.uuid][func_name][0]) <= aggreagate:
            memory.WARNING_COUNT[cam.uuid][func_name].pop(0)
            result = mongodb.alerts.find_one(
                {"create_time": {'$gte': (ts - aggreagate + 1)},
                 "device_id": cam.uuid, "func_name": func_name})
            if result:
                return False
            _save_alert_in_db(alert, image_path, cam)
            alert_data = copy.deepcopy(alert)
            alert_data.pop("_id", None)
            alert_data["create_time"] = ts * 1000
            Middle.CldT.report_alert(alert_data, cam, os.path.join(IMG_BASE_PATH, image_path))
            return True
        return False

    """
    aggregation_time = cam.function.get(func_name, {}).get("aggreagate", functl.get(func_name).get("aggreagate", 600))
    result = mongodb.alerts.find_one(
        {"create_time": {'$gte': (ts - aggregation_time)},
         "device_id": cam.uuid, "func_name": func_name})
    if result:
        return False
    mongodb.alerts.insert_one(alert)
    return True
    """

    """
    # actual reporting
    alert_data = copy.deepcopy(alert)
    alert_data["create_time"] = ts * 1000
    Middle.CldT.report_alert(alert_data, cam, os.path.join(IMG_BASE_PATH, image_path))
    return True
    """


def _save_alert_in_db(alert, image_path, cam):
    alert_image_path = save_alert_img(image_path)
    alert['path'] = alert_image_path
    mongodb.alerts.insert_one(alert)
    if memory.CAMERA_ALERT_QUOTA.get(alert['device_id'], None) or not cam.alert.get("enable", False):
        # 存满停止 或者 本地不存储; 本地mongo仍存储告警数据避免影响聚合周期
        os.remove(os.path.join(IMG_BASE_PATH, alert_image_path))


def save_alert_img(img_path):
    full_path = os.path.join(IMG_BASE_PATH, img_path)

    alert_img_path = "alert" + img_path
    alert_full_path = os.path.join(IMG_BASE_PATH, alert_img_path)

    alert_dir_path = os.path.dirname(alert_full_path)
    if not os.path.exists(alert_dir_path):
        os.makedirs(alert_dir_path)

    shutil.copy(full_path, alert_full_path)
    return alert_img_path
