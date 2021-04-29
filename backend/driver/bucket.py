import os
import re
import logging
import datetime
from collections import defaultdict

import shutil
from PIL import Image, ImageDraw, ImageFont

from backend.driver import clock
from backend.driver import alert as altctl
from backend.driver import camera as camctl
from backend.settings import SYS_CONF
from backend.driver.mongo import mongodb
from backend.middle import Middle
from backend.driver import memory

# RV Storgae move to /var
BASE_PATH = "/var/w2s"
IMG_BASE_PATH = "/var/w2s/media"
ALERT_IMG_BASE_PATH = "/var/w2s/alertmedia"


def save(data, device_id, if_sto_db=True, if_mqtt=True, path_suffix=None):
    cap_dt, _, cap_ts = clock.now()
    save_path = IMG_BASE_PATH + "/{}/image/".format(device_id)
    if path_suffix:
        save_path = IMG_BASE_PATH + "/{}/image/{}/".format(device_id, path_suffix)
    save_name = clock.format_dt(cap_dt) + ".jpg"

    # save on filesystem
    _write(save_path, save_name, data)
    # save on database: images
    img_path = os.path.join(save_path, save_name)

    # 存图片后判断图片是否完整
    try:
        Image.open(img_path).load()
    except Exception as err:
        os.remove(img_path)
        logging.exception(err)
        raise RuntimeError("picture is not valid")

    cam_info = camctl.get_one(device_id)
    if not cam_info.history.get("enable", False):
        if_sto_db = False
    if if_sto_db and memory.CAMERA_HISTORY_QUOTA.get(device_id, False):
        # 这里表示存满停止
        if_sto_db = False

    if if_sto_db:
        # 本地存储,且在存储频率内
        mongodb.images.insert_one({
            "name": save_name,
            "path": img_path,
            "source": device_id,
            "timestamp": cap_ts,
        })
        camctl.update_last_img(device_id)

    if if_mqtt:
        Middle.CldT.report_img(device_id, save_name, img_path, cap_ts * 1000, _file_size_KB(img_path), if_sto_db)

    if SYS_CONF.get("watermark", False):
        _watermark(save_path, save_name, cap_dt, device_id)

    return img_path, if_sto_db


def delete(path, name=None):
    full_path = path
    if name is not None:
        full_path = os.path.join(path, name)
    if os.path.exists(full_path):
        os.remove(full_path)


def delete_many(pathes):
    for p in pathes:
        delete(p)


def latest_images(device_id, amount, promise=False):
    """ WARN: ONLY use promise IF the amount is small,
    otherwise, this function may take VERY LONG TIME
    """
    fetch = mongodb.images.find({"source": device_id}).sort("timestamp", -1).limit(amount)
    if fetch.count() < amount and promise:
        cam = camctl.get_one(device_id)
        for _ in range(amount - fetch.count()):
            save(cam.frame(), cam.uuid)
        fetch = mongodb.images.find({"source": device_id}).sort("timestamp", -1).limit(amount)
        if fetch.count() < amount and promise:
            raise RuntimeError("failed to get camera images")
    return fetch


def clean_by_date():
    for cam in camctl.get_all({})[0]:
        path_list = []
        # delete database: images
        if cam.history.get("sto_days", 0) > 0:
            threshold_dt = datetime.datetime.now() - datetime.timedelta(days=cam.history.get("sto_days", 0))
            logging.info(
                "sweeper history threshold: {} for cam uuid: {}".format(clock.format_dt(threshold_dt), cam.uuid))

            query = {
                "source": cam.uuid,
                "timestamp": {"lt": datetime.datetime.timestamp(threshold_dt)},
            }
            fetch = mongodb.images.find(query)
            path_list = [{"path": it["path"], "timestamp": it["timestamp"] * 1000} for it in fetch]
            mongodb.images.delete_many(query)

        if cam.alert.get("sto_days", 0) > 0:
            # delete database: alerts
            threshold_dt = datetime.datetime.now() - datetime.timedelta(days=cam.alert.get("sto_days", 0))
            logging.info("sweeper alert threshold: {} for cam uuid: {}".format(clock.format_dt(threshold_dt), cam.uuid))

            query = {
                "device_id": cam.uuid,
                "create_time": {"lt": datetime.datetime.timestamp(threshold_dt)},
            }
            fetch = mongodb.alerts.find(query)
            alert_path_list = [{"path": os.path.join(BASE_PATH, it["path"]), "timestamp": it["create_time"] * 1000} for
                               it in fetch]
            altctl.delete(query)

            # delete on filesystem
            path_list += alert_path_list

        for p in path_list:
            delete(p["path"])

        Middle.CldT.report_img_del(cam.uuid, path_list)


def clean_by_quota(quota):
    def get_disk_percent():
        _percent = shutil.disk_usage(BASE_PATH)
        _percent = int(round(_percent.free / _percent.total * 100))
        logging.warning("current disk free: %s", _percent)
        return _percent

    all_cam = camctl.get_all({})[0]
    for cam in all_cam:
        _clean_cam_history_by_quota(cam)
        _clean_cam_alert_by_quota(cam)
    while get_disk_percent() < quota:
        logging.info("disk percentage exceeds quota")
        clean_num = _clean_oldest_imgs(SYS_CONF.get("clean_img_num", 100))
        if clean_num is None or clean_num == 0:
            break
    while get_disk_percent() < quota:
        logging.warning("disk percentage still exceeds quota after clean history image. now clean alert")
        clean_num = _clean_oldest_alerts(SYS_CONF.get("clean_alert_num", 100))
        if clean_num is None or clean_num == 0:
            break

    logging.warning("clean by quota done")


def _clean_oldest_imgs(clean_num):
    # 清理最旧的历史图片
    fetch = mongodb.images.find({}).sort("timestamp", 1).limit(clean_num)
    cam_paths = defaultdict(list)
    paths = []
    db_ids = []
    for img in fetch:
        cam_paths[img["source"]].append({"path": img["path"], "timestamp": img["timestamp"] * 1000})
        paths.append(img["path"])
        db_ids.append(img["_id"])

    if paths:
        logging.warning("removing... %s", paths)
        mongodb.images.delete_many({"_id": {"$in": db_ids}})
        for path in paths:
            delete(path)
        for cam_uuid, imgs in cam_paths.items():
            Middle.CldT.report_img_del(cam_uuid, imgs)
        logging.warning("removing history img done")
        return len(paths)


def _clean_oldest_alerts(clean_num):
    fetch = mongodb.alerts.find({}).sort("timestamp", 1).limit(clean_num)
    paths = []
    db_ids = []
    for alt in fetch:
        paths.append(os.path.join(BASE_PATH, alt["path"]))
        db_ids.append(alt["_id"])

    if paths:
        logging.warning("removing alerts imgs...%s", paths)
        mongodb.alerts.delete_many({"_id": {"$in": db_ids}})
        for path in paths:
            delete(path)
        logging.warning("removing alerts img done")
        return len(paths)


def _clean_cam_history_by_quota(cam_info):
    history_quota = cam_info.history.get("sto_cap")
    if history_quota is None or history_quota <= 0:
        return

    while _path_disk_usage_GB(os.path.join(IMG_BASE_PATH, cam_info.uuid)) > history_quota:
        if cam_info.history.get("storage", 0) == 1:
            # 存满停止
            memory.CAMERA_HISTORY_QUOTA[cam_info.uuid] = True
            return
        fetch = mongodb.images.find({"source": cam_info.uuid}).sort("timestamp", 1).limit(3)
        path_list = [{"path": it["path"], "timestamp": it["timestamp"] * 1000} for it in fetch]
        if len(path_list) > 0:
            paths = [pl['path'] for pl in path_list]
            # delete database: images index
            logging.warning("removing... %s", paths)
            mongodb.images.delete_many({"path": {"$in": paths}})
            # delete on filelsystem
            for p in paths:
                delete(p)
            Middle.CldT.report_img_del(cam_info.uuid, path_list)

    memory.CAMERA_HISTORY_QUOTA.pop(cam_info.uuid, None)


def _clean_cam_alert_by_quota(cam_info):
    alert_quota = cam_info.alert.get("sto_cap")
    if alert_quota is None or alert_quota <= 0:
        return

    while _path_disk_usage_GB(os.path.join(ALERT_IMG_BASE_PATH, cam_info.uuid)) > alert_quota:
        if cam_info.alert.get("storage", 0) == 1:
            # 存满停止
            memory.CAMERA_ALERT_QUOTA[cam_info.uuid] = True
            return
        fetch = mongodb.alerts.find({"device_id": cam_info.uuid}).sort("timestamp", 1).limit(3)
        path_list = [it["path"] for it in fetch]
        if len(path_list) > 0:
            # delete database: images index
            logging.warning("removing... %s", path_list)
            altctl.delete({"path": {"$in": path_list}})
            # delete on filelsystem
            for path in path_list:
                delete(os.path.join(BASE_PATH, path))
    memory.CAMERA_ALERT_QUOTA.pop(cam_info.uuid, None)


def clean_history():
    logging.info("clean all history images and alerts")
    # clean images
    fetch = mongodb.images.find({})
    path_list = [it["path"] for it in fetch]

    fetch = mongodb.alerts.find({})
    alert_path_list = [os.path.join(BASE_PATH, it["path"]) for it in fetch]
    path_list += alert_path_list

    for p in path_list:
        delete(p)
    mongodb.images.delete_many({})
    # clean alerts
    # TODO report to asp
    mongodb.alerts.delete_many({})
    memory.CAMERA_ALERT_QUOTA = {}
    memory.CAMERA_HISTORY_QUOTA = {}
    logging.info("all alerts and images are cleaned!")


def _write(path, name, data):
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, name), 'wb') as f:
        f.write(data)


AFont = ImageFont.truetype("/app/font_wqhei.ttf", size=SYS_CONF.get("watermark_size", 20))


def _watermark(path, name, dt, dev_id):
    full_path = os.path.join(path, name)
    split = clock.format_dt(dt).split('-')
    time_string = "-".join(split[0:3]) + " " + ":".join(split[3:6])
    cam = camctl.get_one(dev_id)
    loc_string = "None"
    if cam is not None:
        loc_string = cam.location

    frame = Image.open(full_path)
    draw = ImageDraw.Draw(frame)
    width, height = frame.size

    # time string
    w, h = draw.textsize(time_string, font=AFont)
    x0, y0 = (30, 30)
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill="#FFFFFF")
    draw.text((x0, y0), time_string, font=AFont, fill="#000000")

    # location string
    w, h = draw.textsize(loc_string, font=AFont)
    x0, y0 = (10, height - h - 20)
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill="#FFFFFF")
    draw.text((x0, y0), loc_string, font=AFont, fill="#000000")

    delete(full_path)
    frame.save(full_path, 'jpeg')


def _file_size_KB(file_path):
    return os.path.getsize(file_path) / 1024.0


def _path_disk_usage_GB(path_):
    response = os.popen(f'du -sh {path_}')
    str_size = response.read().split()[0]
    f_size = float(re.findall(r'[.\d]+', str_size)[0])
    size_unit = re.findall(r'[A-Z]', str_size)[0]
    if size_unit == 'K':
        f_size = round(f_size / 1024 / 1024, 2)
    if size_unit == 'M':
        f_size = round(f_size / 1024, 2)
    if size_unit == 'T':
        f_size = round(f_size * 1024, 2)
    return f_size
