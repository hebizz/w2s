import hashlib
import logging

from backend.driver import clock
from backend.settings import SYS_CONF
from backend.model.camera import Camera
from backend.driver.mongo import mongodb, resize_mongo_result, mongo_id_to_str
from backend.driver import function as functl
from backend.task import RT
from backend.driver import memory
from backend.middle import Middle
from backend.model import device


def get_one(device_id):
    if memory.CAMERA is None:
        raise RuntimeError("memory.CAMERA is empty!")
    for cam in memory.CAMERA[0]:
        if cam.uuid == device_id:
            return cam
    raise RuntimeError("no such camera ({}) in database".format(device_id))


def get_rand_one():
    fetch = mongodb.device.find_one()
    if fetch is None:
        raise RuntimeError("no such camera in database")
    return Camera(mongo_id_to_str(fetch))


def get_all(query, limit=0, offset=0):
    memory.CAMERA = _get_all({})
    if query is None or query == {}:
        return memory.CAMERA
    return _get_all(query, limit, offset)


def _get_all(query, limit=0, offset=0):
    query['type'] = "camera"
    fetch = mongodb.device.find(query)
    if fetch is None:
        logging.warning("camera-all (%s) returns empty", query)
        return [], 0
    results = resize_mongo_result(fetch, limit=limit, offset=offset)
    return [Camera(mongo_id_to_str(r)) for r in results], fetch.count()


def if_sto_img(cam_info):
    if not cam_info.history.get("enable", False):
        return False

    if last_img_time(cam_info.uuid) is None:
        return True

    _, _, ts = clock.now()
    return ts - last_img_time(cam_info.uuid) > (cam_info.history.get('sto_freq') - 1)


def last_img_time(device_id):
    return memory.CAMERA_LAST_IMG.get(device_id)


def update_last_img(device_id):
    _, _, ts = clock.now()
    memory.CAMERA_LAST_IMG[device_id] = ts


def if_upload_img(cam_info):
    if not cam_info.upload.get("history_enable", False):
        return False

    if not cam_info.history.get("enable") and cam_info.upload.get("img_type") == "local":
        return False

    if last_img_upload(cam_info.uuid) is None:
        return True

    _, _, ts = clock.now()
    return ts - last_img_upload(cam_info.uuid) > (cam_info.upload.get("img_freq") - 1)


def update_last_upload(device_id):
    _, _, ts = clock.now()
    memory.CAMERA_LAST_UPLOAD[device_id] = ts


def last_img_upload(device_id):
    return memory.CAMERA_LAST_UPLOAD.get(device_id)


def add(cam_type, address, username, password, cam_uuid=None, cam_port=554, cam_channel=1):
    for c in get_all({})[0]:  # take this structure to handle more complicated scenario
        if c.cam_address == address and c.cam_channel == cam_channel:
            return c.uuid

    _, _, ts = clock.now()
    init_func_list = {}
    for f, v in functl.get("").items():
        init_func_list[f] = {
            "enable": True,
            "zones": [],
            "reverse": False,
            "detection_cycle": v["detection_cycle"],
            "alert_level": v["alert_level"],
            "threshold": v["init_threshold"],
            "aggreagate": v["aggreagate"],
            "aggreagate_times": v["aggreagate_times"],
        }

    if not cam_uuid:
        cam_uuid = _gen_id(address)
    camera_data = {
        "uuid": cam_uuid,
        "name": address,
        "edgex_name": "",
        "type": "camera",
        "cam_type": cam_type,
        "cam_address": address,
        "cam_port": cam_port,
        "cam_username": username,
        "cam_passwd": password,
        "cam_channel": cam_channel,
        "host_id": SYS_CONF['host_id'],
        "host_ip": SYS_CONF['host_ip'],
        "location": '未指定',
        "wakeup_time": ts,
        "status": "normal",
        "interval": SYS_CONF['default_capture_interval'],
        "function": init_func_list,
        "flavour": False,
        "history": SYS_CONF['history'],
        "alert": SYS_CONF["alert"],
        "upload": SYS_CONF["upload"],
        "detected_times": [ts],
    }
    mongodb.device.insert_one(camera_data)
    get_all({})
    warning_count = {camera_data["uuid"]: {func: [] for func in functl.get("").keys()}}
    memory.WARNING_COUNT.update(warning_count)
    # RT.insert_subtask(camera_data['uuid'])

    Middle.RT.insert_subtask(camera_data['uuid'])
    if device.is_edge_proxy():
        Middle.CldT.report_cam_setting(cam_uuid)
        Middle.CldT.report_function_cam(cam_uuid)


def init_func(device_id):
    if device_id:
        init_func_list = {}
        for f, v in functl.get("").items():
            init_func_list[f] = {
                "enable": True,
                "zones": [],
                "reverse": False,
                "detection_cycle": v["detection_cycle"],
                "alert_level": v["alert_level"],
                "threshold": v["init_threshold"],
                "aggreagate": v["aggreagate"],
                "aggreagate_times": v["aggreagate_times"],
            }
        update(device_id, {"function": init_func_list})


def update(device_id, data):
    mongodb.device.update_one({'uuid': device_id}, {'$set': data})
    if device.is_edge_proxy():
        Middle.CldT.report_cam_setting(device_id)
        Middle.CldT.report_function_cam(device_id)
    get_all({})
    return get_one(device_id)


def update_all(data):
    mongodb.device.update_many({}, {'$set': data})
    if device.is_edge_proxy():
        Middle.CldT.report_setting()
        Middle.CldT.report_function()


def delete(device_id):
    Middle.RT.remove_subtask(device_id)
    mongodb.device.delete_one({"uuid": device_id})
    memory.WARNING_COUNT.pop(device_id)
    get_all({})
    mongodb.images.delete_many({"source": device_id})
    mongodb.alerts.delete_many({"device_id": device_id})
    Middle.CldT.report_cam_del(device_id)
    memory.CAMERA_HISTORY_QUOTA.pop(device_id, None)
    memory.CAMERA_ALERT_QUOTA.pop(device_id, None)


def summary():
    results = mongodb.device.find()
    normal_devices = []
    abnormal_devices = []
    for result in results:
        if result.get("status", "abnormal") == "normal":
            normal_devices.append(result)
        else:
            abnormal_devices.append(result)
    data = {
        "total_devices_count": len(normal_devices) + len(abnormal_devices),
        "normal_devices_count": len(normal_devices),
        "abnormal_devices_count": len(abnormal_devices)
    }
    return data


def _gen_id(address):
    return hashlib.md5(address.encode('utf-8')).hexdigest()
    # return str(uuid.uuid4())  # deprecated
