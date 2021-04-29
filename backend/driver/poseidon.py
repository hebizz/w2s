import os
import json
import yaml
import logging
import requests
from backend.settings import SYS_CONF


def get_poseidon_id():
    if os.path.exists(SYS_CONF["poseidon_id_path"]):
        with open(SYS_CONF["poseidon_id_path"], "r") as f:
            node_id = f.read()
    elif os.path.exists(SYS_CONF["jxcore_id_path"]):
        with open(SYS_CONF["jxcore_id_path"]) as f:
            node_id = f.read()
    else:
        raise RuntimeError("not found poseidon id to register!!!")
    SYS_CONF["host_id"] = node_id.strip()
    return node_id.strip()


def get_ip_info():
    # get eth0, mac, tun0 from poseidon
    res = requests.get(SYS_CONF["get_ip_url"])
    if res.status_code != 200:
        raise RuntimeError("can not get poseidon ip")
    data = json.loads(res.text)["data"]
    return data.get("eth0", ""), data.get("mac", ""), data.get("tun0", "")

def get_host_ip():
    ip, _, _ = get_ip_info()
    return ip


def register_device(node_id, eth0, mac, tun0, port):
    with open(SYS_CONF["cloud_point_path"]) as f:
        temp = yaml.load(f.read())
    cloud_point_address = "{}/api/v1/edge/register".format(temp["address"])
    headers = {"ASPAccess": temp["access"], "ASPPass": temp["pass"]}
    logging.info(cloud_point_address)
    logging.info(headers)

    data = {
        "uuid": node_id,
        "mac": mac,  # mac地址
        "tun0": tun0,  # tun0 IP
        "eth0": eth0,  # eth0 IP
        "port": port  # http服务端口号
    }

    # register interface send to cloud point
    logging.info("register data: {}".format(data))
    try:
        response = requests.post(cloud_point_address, json=data, headers=headers)
        logging.info("register reponse: {}".format(response.text))
        asp_data = {
            "status": response.status_code,
            "msg": response.text
        }
    except Exception as err:
        logging.error(err)
        asp_data = {
            "status": 500,
            "msg": "注册地址或key错误"
        }
    asp_response = requests.post(SYS_CONF["webconfig_addr"], json=asp_data)
    logging.info("report register status to webconfig: {}".format(asp_response.text))
    if asp_data["status"] != 200:
        raise RuntimeError("register device fail!!!")
    if SYS_CONF["mqtt"]["addr"] is None:
        SYS_CONF["mqtt"]["addr"] = temp["address"].split("//")[1].split(":")[0]
    logging.info("mqtt addr: {}".format(SYS_CONF["mqtt"]))


def update_time(date=None):
    if date:
        res = requests.post(SYS_CONF["update_time_url"], data={"date": date})
    else:
        res = requests.put(SYS_CONF["update_time_url"])
    msg = json.loads(res.text)["msg"]
    data = json.loads(res.text)["data"]
    if res.status_code != 200:
        logging.info("update time fail: {}".format(msg))
    return msg, data
