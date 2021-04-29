import base64
import logging
import json
import requests
import cv2

from backend.settings import SYS_CONF
from backend.driver import clock
from backend.driver import alert as alctl
from backend.driver import function as functl
from backend.driver.mongo import mongodb

FUNC_BBOX_COLOR = {
    "move": (255, 0, 255),
    "fire": (255, 255, 0),
    "no_helmet": (255, 0, 0),
    "smoke": (0, 255, 0),
    "pata": (0, 0, 255),
    "restrict": (0, 255, 255),
    "machinery": (255, 255, 255)
}


def export(parse_results, pic_path, cam):
    export_url = SYS_CONF["exporter"].get("url")
    if export_url is None:
        raise RuntimeError("export url is None!")

    alert_allowed, _ = alctl.allowed_alert_type()
    img = cv2.imread(pic_path)
    cst_dt, utc_dt, ts = clock.now()

    cor = [20, 20]
    for func_name in alert_allowed:
        color = FUNC_BBOX_COLOR[func_name]
        cv2.putText(img, func_name, tuple(cor), cv2.FONT_HERSHEY_COMPLEX, 0.5, color, 1)
        cor[1] = cor[1] + 15

    export_data = {
        "device_id": cam.uuid,
        "device_name": cam.name,
        "host_id": SYS_CONF.get("host_id"),
        "host_ip": SYS_CONF.get("host_ip"),
        "timestamp": clock.format_dt_standard(utc_dt),
        "location": cam.location,
        "alert": [],
        "image": '',
    }
    for func_name, alert_info in parse_results.items():
        if func_name not in alert_allowed:
            logging.info("alert(%s) raise, but will not export", func_name)
            continue
        aggregation_time = functl.get(func_name).get("aggreagate", 600)
        result = mongodb.alerts.find_one(
            {"create_time": {'$gte': (ts - aggregation_time)},
             "device_id": cam.uuid, "func_name": func_name})

        if not result:
            for position in alert_info:
                probability = str(position["probability"])
                xmin = int(position["xmin"])
                ymin = int(position["ymin"])
                xmax = int(position["xmax"])
                ymax = int(position["ymax"])
                export_data["alert"].append([func_name, probability, str(xmin), str(ymin), str(xmax), str(ymax)])
                img = cv2.rectangle(img, (xmin, ymin), (xmax, ymax), FUNC_BBOX_COLOR[func_name], 4)
    b64_str = cv2.imencode('.jpg', img)[1].tostring()
    b64_img = base64.b64encode(b64_str)
    export_data["image"] = str(b64_img, encoding='utf-8')
    requests_data = json.dumps(export_data)
    try:
        if export_data["alert"] != []:
            response = requests.post(export_url, data=requests_data)
            logging.info(response)
    except Exception as err:
        logging.error("export data failed!")
