import logging
import threading
import json
import time
import traceback
import base64
import os
import platform
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from backend.settings import SYS_CONF
from backend.driver import bucket as bktctl
from backend.driver import poseidon as psdctl
from backend.driver import camera as camctl
from backend.driver import function as functl
from backend.driver import evevt as evectl
from backend.driver import recogn as rcgctl
from backend.driver import clock as clkctl
from backend.driver.mongo import mongodb
from backend.model import device
from backend.task.abstract import AbstractTask


class Cloud(AbstractTask):
    """
    通过mqtt跟云端交互
    """
    topic_sub_init = "{uuid}/init"
    topic_sub_setting = "{uuid}/setting"
    topic_sub_time = "{uuid}/time"
    topic_sub_cam_add = "{uuid}/cam/add"
    topic_sub_cam_setting = "{uuid}/cam/setting"
    topic_sub_cam_del = "{uuid}/cam/del"
    topic_sub_function_batch = "{uuid}/function/batch"
    topic_sub_function_cam = "{uuid}/function/cam"
    topic_sub_function = "{uuid}/function"
    topic_sub_snap = "{uuid}/snap"
    topic_sub_stream = "{uuid}/stream"
    topic_sub_stream_close = "{uuid}/stream/close"
    topic_sub_cam_back = "{uuid}/cam/back"
    topic_sub_cam_back_close = "{uuid}/cam/back/close"
    topic_sub_plc_add = "{uuid}/plc/add"
    topic_sub_plc_del = "{uuid}/plc/del"
    topic_sub_plc = "{uuid}/plc"
    topic_sub_plc_update = "{uuid}/plc/update"

    topic_pub_health = "edge/{uuid}/health"
    topic_pub_event = "edge/{uuid}/event"
    topic_pub_setting = "edge/{uuid}/setting"
    topic_pub_time = "edge/{uuid}/time"
    topic_pub_cam_add = "edge/{uuid}/cam/add"
    topic_pub_cam_setting = "edge/{uuid}/cam/setting"
    topic_pub_cam_del = "edge/{uuid}/cam/del"
    topic_pub_function = "edge/{uuid}/function"
    topic_pub_function_batch = "edge/{uuid}/function/batch"
    topic_pub_function_cam = "edge/{uuid}/function/cam"
    topic_pub_snap = "edge/{uuid}/snap"
    topic_pub_alert = "edge/{uuid}/alert"
    topic_pub_stream = "edge/{uuid}/stream"
    topic_pub_cam_back = "edge/{uuid}/cam/back"
    topic_pub_img = "edge/{uuid}/img"
    topic_pub_img_del = "edge/{uuid}/img/del"
    topic_pub_plc_add = "edge/{uuid}/plc/add"
    topic_pub_plc_del = "edge/{uuid}/plc/del"
    topic_pub_plc = "edge/{uuid}/plc"
    topic_pub_plc_update = "edge/{uuid}/plc/update"

    def __init__(self):
        super().__init__("mqtt")
        self.mqtt_client = None

    def run(self):
        while True:
            try:
                self._run()
            except Exception:
                logging.exception("Mqtt cloud task run fail. retry in %d.", self.fail_interval)
            time.sleep(self.fail_interval)

    def _run(self):
        try:
            node_id = psdctl.get_poseidon_id()
            eth0, mac, tun0 = psdctl.get_ip_info()
            psdctl.register_device(node_id, eth0, mac, tun0, SYS_CONF["external_port"])
            logging.info("register success {}".format(node_id))
        except Exception as err:
            logging.exception(err)
            logging.error("register to cloud failed")
            return

        Cloud.format_topics(node_id)  # 格式化topics

        t = threading.Thread(target=self.t_report_health)
        t.setDaemon(True)
        t.start()

        e = threading.Thread(target=self.report_event)
        e.setDaemon(True)
        e.start()

        try:
            # self.mqtt_client = mqtt.MqttClient(client_id=node_id, clean_session=False , host=SYS_CONF["mqtt"]["addr"], port=SYS_CONF["mqtt"]["port"])
            self.mqtt_client = mqtt.Client(client_id=node_id, clean_session=False)
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.connect(host=SYS_CONF["mqtt"]["addr"], port=SYS_CONF["mqtt"]["port"])
            self.mqtt_client.on_log = self.on_log
            self.mqtt_client.loop_forever()
        except:
            logging.error(traceback.format_exc())
            return

    @classmethod
    def format_topics(cls, node_id):
        topics = ("topic_sub_init", "topic_sub_setting", "topic_sub_time", "topic_sub_cam_add", "topic_sub_cam_setting",
                  "topic_sub_cam_del",
                  "topic_sub_function_batch", "topic_sub_function_cam", "topic_sub_function", "topic_sub_snap",
                  "topic_sub_stream",
                  "topic_sub_stream_close",
                  "topic_sub_cam_back", "topic_sub_cam_back_close", "topic_sub_plc_add", "topic_sub_plc_del",
                  "topic_sub_plc",
                  "topic_sub_plc_update",
                  "topic_pub_setting", "topic_pub_event", "topic_pub_cam_add", "topic_pub_time",
                  "topic_pub_cam_setting",
                  "topic_pub_cam_del",
                  "topic_pub_function", "topic_pub_function_batch", "topic_pub_function_cam", "topic_pub_alert",
                  "topic_pub_snap", "topic_pub_stream", "topic_pub_cam_back", "topic_pub_img", "topic_pub_img_del",
                  "topic_pub_health",
                  "topic_pub_plc_add", "topic_pub_plc_del", "topic_pub_plc_update")

        for topic in topics:
            if hasattr(cls, topic):
                setattr(cls, topic, getattr(cls, topic).format(uuid=node_id))

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """
        mqtt 连接成功的回调
        """
        logging.info("mqtt connect(or reconnect) success")

        try:
            sub_topic_funcs = {
                Cloud.topic_sub_init: self.on_init,
                Cloud.topic_sub_setting: self.on_setting,
                Cloud.topic_sub_time: self.on_date,
                Cloud.topic_sub_cam_add: self.on_cam_add,
                Cloud.topic_sub_cam_setting: self.on_cam_setting,
                Cloud.topic_sub_cam_del: self.on_cam_del,
                Cloud.topic_sub_function_batch: self.on_function_batch,
                Cloud.topic_sub_function_cam: self.on_function_cam,
                Cloud.topic_sub_function: self.on_function,
                Cloud.topic_sub_snap: self.on_snap,
                Cloud.topic_sub_stream: self.on_stream,
                Cloud.topic_sub_stream_close: self.on_stream_close,
                Cloud.topic_sub_cam_back: self.on_cam_back,
                Cloud.topic_sub_cam_back_close: self.on_cam_back_close,
                Cloud.topic_sub_plc_add: self.on_plc_add,
                Cloud.topic_sub_plc_del: self.on_plc_del,
                Cloud.topic_sub_plc: self.on_plc,
                Cloud.topic_sub_plc_update: self.on_plc_update
            }

            def callback_warpper(callback):
                def _warpper(client, userdata, msg):
                    try:
                        logging.info("callback func name: {}, receive data: {}".format(callback.__name__, msg.payload))
                        # data = eval(str(msg.payload, encoding="utf-8"))
                        data = json.loads(str(msg.payload.decode("utf-8")))
                        callback(data)
                    except:
                        logging.error(traceback.format_exc())

                return _warpper

            # 边侧启动并连接成功后向云侧主动报告一次
            self.report_function()
            self.report_setting()

            # 这里断线重连需要重新subscribe
            for topic, callback in sub_topic_funcs.items():
                logging.info("mqtt subscribe topic {}".format(topic))
                client.subscribe(topic=topic, qos=2)
                client.message_callback_add(sub=topic, callback=callback_warpper(callback))
        except:
            logging.exception("mqtt subscribe fail")

    def on_disconnect(self, client, userdata=None, rc=None, properties=None):
        logging.warn("mqtt disconnect !!!")

    def on_log(self, client, userdata, level, buf):
        logging.info("mq msg: {} {}".format(level, buf))

    def on_init(self, data):
        '''
        设备初始化，用于asp添加设备后又删除的情况
        1. 将function均设置为默认值，并report function
        '''
        logging.info("device init from mqtt: {}".format(data))
        camctl.init_func(data.get("device_id", None))
        self.report_function()

    def on_setting(self, data):
        """
        修改设备设置,
        2020/12/24-综合平台V1.1.0版本对于服务器/盒子类设备废弃此设置
        2021/01/04-对于移动站/智慧眼产品，此设置生效
        """
        logging.info("change device setting: {}".format(data))

        if device.is_edge_ipc():
            msg_id = data.pop("msg_id")
            camctl.update_all(data)

        self.report_setting(msg_id)

    def on_date(self, data):
        """
        设备校时
        """
        logging.info("update time setting: {}".format(data))

        msg_id = data.pop("msg_id")
        if data["method"] == "auto":
            msg, date = psdctl.update_time()
        else:
            msg, date = psdctl.update_time(data["daytime"])

        self.report_date(msg, date, msg_id)

    def on_cam_add(self, data):
        """
        添加普通摄像头
        """
        logging.info("add cam: {}".format(data))

        msg_id = data["msg_id"]

        if device.is_edge_ipc():
            self.publish(Cloud.topic_pub_cam_add, {
                "msg_id": msg_id,
                "desc": "该设备不支持添加摄像头"  # success表示成功，失败传原因
            })
            return

        ip = data["ip"]
        username = data["username"]
        password = data["password"]
        cam_type = data["cam_type"]
        cam_uuid = data["cam_uuid"]
        cam_port = data["cam_port"]
        cam_channel = data["cam_channel"]

        desc = "success"
        uuid = ""
        try:
            uuid = camctl.add(cam_type, ip, username, password, cam_uuid, cam_port, cam_channel)
        except Exception as e:
            desc = "failed: {}".format(e)

        logging.info("add new cam: {} {} {} {} {} {} {} {}".format(cam_type, ip, username, password, cam_uuid, cam_port,
                                                                   cam_channel, desc))
        resp_data = {
            "msg_id": msg_id,  # 带着上面的msgId
            "desc": desc,  # success表示成功，失败传原因
            "uuid": uuid,  # 异常处理时云端需要
        }
        self.publish(Cloud.topic_pub_cam_add, resp_data)

    def on_cam_setting(self, data):
        """
        普通摄像头更新设置
        """
        logging.info("change cam setting: {}".format(data))

        msg_id = data.pop("msg_id")
        cam_uuid = data.pop("cam_uuid")

        camctl.update(cam_uuid, data)
        self.report_cam_setting(cam_uuid=cam_uuid, msg_id=msg_id)

    def on_cam_del(self, data):
        """
        删除普通摄像头
        data: [{ # 使用数组支持批量
                "cam_uuid":"", #摄像头设备编号
            }]
        """
        logging.info("begin to delete cams {}".format(data))

        if device.is_edge_ipc():
            logging.error('edge ipc, not support of del cam')
            return

        for elem in data:
            cam_uuid = elem["cam_uuid"]
            camctl.delete(cam_uuid)
            logging.info("delete cam {}".format(cam_uuid))

    def on_function_batch(self, data):
        """
        批量更新边侧摄像头某种类型的告警设置
        """
        logging.info("function batch setting: {}".format(data))

        msg_id = data["msg_id"]
        func_name = data["func_name"]
        enable = data["enable"]
        aggreagate = data["aggreagate"]
        device_ids = data["device_ids"]
        update_server = data["update_server"]

        desc = "success"
        if update_server:
            # 修改function表的设置
            function = functl.get(func_name)
            if function:
                function["enable"] = enable
                function["aggreagate"] = aggreagate
                functl.update_all({func_name: function})
            else:
                desc = "func_name {} not support".format(func_name)

        # 依次处理每个设备
        for device_id in device_ids:
            cam_info = camctl.get_one(device_id)
            function = cam_info.function
            one_function = function.get(func_name)
            if one_function:
                one_function["enable"] = enable
                one_function["aggreagate"] = aggreagate
                function[func_name] = one_function
                camctl.update(device_id, {"function": function})
            else:
                if desc == "success":
                    desc = ""
                desc += "device {} not support func_name {}".format(device_id, func_name)

        resp_data = {
            "msg_id": msg_id,  # 带着上面的msgId
            "desc": desc  # success表示成功，失败传原因
        }
        self.publish(Cloud.topic_pub_function_batch, resp_data)

    def on_function_cam(self, data):
        """
        全量更新摄像头的告警设置
        """
        logging.info("function cam setting: {}".format(data))

        msg_id = data["msg_id"]
        function = data["function"]
        device_ids = data["device_ids"]

        for device_id in device_ids:
            cam_function = camctl.get_one(device_id).function
            for func_name in cam_function:
                if func_name in function:
                    cam_function[func_name] = function[func_name]
            logging.info("change cam {} function: {}".format(device_id, cam_function))
            camctl.update(device_id, {"function": cam_function})

        self.report_function_cam(device_ids, msg_id)

    def on_function(self, data):
        # 目前该function仅用于TD201/202
        # 阵列和盒子等代理使用function batch和function cam，其中function cam应该废弃变成function
        logging.info("function setting: {}".format(data))

        msg_id = data.pop("msg_id", "")
        func_name = data.pop("func_name")

        if device.is_edge_ipc():
            cam = device.get_edge_ipc_cam()
        elif "device_id" in data:
            cam = camctl.get_one(data["device_id"])
        else:
            logging.info("unexpected function setting got: %s", data)
            self.report_function(msg_id)
            return
        cam_function = cam.function
        if cam_function and func_name in cam_function:
            for k, v in data.items():
                cam_function[func_name][k] = v

            logging.info("change cam {} function: {}".format(cam.uuid, cam_function))
            camctl.update(cam.uuid, {"function": cam_function})
        self.report_function(msg_id, data.pop("device_id", None))

    def on_snap(self, data):
        """
        手动拍照
        """
        msg_id = data["msg_id"]
        device_id = data["device_id"]
        cam = camctl.get_one(device_id)
        # snap image will delete by routine, add suffix to avoid
        saved_path, if_sto_db = bktctl.save(cam.frame(), device_id, True, False, "snap")

        resp_data = {
            "msg_id": msg_id,  # 请求中的msg_id
            "name": "",  # 图片名称
            "device_id": device_id,  # 设备ID
            "create_time": clkctl._unix13ts(),  # 1 3位时间戳
            "alert": [],  # ai识别产生的告警列表
        }

        if if_sto_db and cam.history and cam.history.get("upload", "") == "local":
            resp_data["path"] = saved_path.split("w2s/")[1]
        else:
            with open(saved_path, "rb") as f:
                resp_data["img_str"] = str(base64.b64encode(f.read()), encoding='utf-8')

        function_list = rcgctl.period_function_filter(cam, mode="manual")
        model_list = rcgctl.ai_pointer_filter(function_list)
        try:
            logging.info("%s manual photo: start ai recognize, function is : %s, model is : %s",
                         device_id, str(function_list), str(model_list))
            parse_results = rcgctl.recognize(saved_path, device_id, function_list, model_list)
            if parse_results:
                for k, v in parse_results.items():
                    res = {
                        "func_name": k,  # AI类型
                        "title": functl.get(k).get("title", ""),  # 告警名称
                        "alert_position": v,  # 告警框列表，每个框是一个矩形
                        "create_time": clkctl._unix13ts(),  # 13位时间戳
                        "level": cam.function.get(k, {}).get("alert_level", functl.get(k).get("alert_level", ""))
                        # general/urgent
                    }
                    resp_data["alert"].append(res)
                self.publish(Cloud.topic_pub_snap, resp_data)
            else:
                self.publish(Cloud.topic_pub_snap, resp_data)
            logging.info("%s manual photo success: %s", device_id, resp_data)

        except Exception as err:
            logging.error("%s manual photo ai failed: %s", device_id, err)
            self.publish(Cloud.topic_pub_snap, resp_data)
        finally:
            if not if_sto_db:
                bktctl.delete(saved_path)

    def on_stream(self, data):
        """
        摄像头推流
        """
        logging.info("open streaming: {}".format(data))

        msg_id = data["msg_id"]
        device_id = data["device_id"]

        stream = ""
        desc = "success"
        try:
            cam = camctl.get_one(device_id)
            cam.open_stream()
            stream = cam.preview_stream()
        except Exception as err:
            logging.exception("failed to open streaming on {} {}".format(device_id, err))
            desc = str(err)

        resp_data = {
            "msg_id": msg_id,
            "stream": stream,  # url
            "desc": desc,
        }
        self.publish(Cloud.topic_pub_stream, resp_data)

    def on_stream_close(self, data):
        """
        摄像头关闭推流
        """
        logging.info("close streaming: {}".format(data))

        device_id = data.get("device_id")
        try:
            cam = camctl.get_one(device_id)
            cam.close_stream()
        except Exception as err:
            logging.exception(err)
            logging.error("failed to stop streaming on {}".format(device_id))
            return

        logging.info("stop streaming on {} success".format(device_id))

    def on_cam_back(self, data):
        """
        摄像头录像回放
        """
        logging.info("open back streaming: {}".format(data))

        msg_id = data["msg_id"]
        device_id = data["device_id"]
        start = int(data["start"] / 1000)
        end = int(data["end"] / 1000)

        starttime = time.strftime("%Y%m%dt%H%M%Sz", time.localtime(start))
        endtime = time.strftime("%Y%m%dt%H%M%Sz", time.localtime(end))

        stream = ""
        desc = "success"
        try:
            cam = camctl.get_one(device_id)
            cam.open_back_stream(starttime, endtime)
            stream = cam.preview_stream(back=True)
        except Exception as err:
            logging.exception("failed to start back on {} {}".format(device_id, err))
            desc = str(err)

        resp_data = {
            "msg_id": msg_id,
            "stream": stream,  # url
            "desc": desc,
        }
        self.publish(Cloud.topic_pub_cam_back, resp_data)

    def on_cam_back_close(self, data):
        """
        摄像头关闭回放
        """
        logging.info("close back streaming: {}".format(data))

        device_id = data.get("device_id")
        try:
            cam = camctl.get_one(device_id)
            cam.close_back_stream()
        except Exception as err:
            logging.exception(err)
            logging.error("failed to stop back streaming on {}".format(device_id))
            return

        logging.info("stop back streaming on {} success".format(device_id))

    def on_plc_add(self, data):
        """
        增加plc设备
        """
        if platform.machine().split("_")[0] != "x86":
            self.publish(Cloud.topic_pub_plc_add, {
                "msg_id": data.get("msg_id", ""),
                "desc": "该设备不支持添加PLC控制器"
            })
            return
        plc_addr = data.get("plc_addr")
        plc_msg = list(data.get("plc_msg"))
        resp_data = {
            "desc": "success",
        }
        if data.get("msg_id", None):
            resp_data["msg_id"] = data["msg_id"]
        if mongodb.plc.find_one({"plc_addr": plc_addr}):
            resp_data["desc"] = "plc地址已被注册"
            logging.info(resp_data["desc"])
            self.publish(Cloud.topic_pub_plc_add, resp_data)
            return
        # 控制模式,默认102,103
        for p in plc_msg:
            plc_switch_cmd = "./{} {} {} {}".format(SYS_CONF["default_plc"], plc_addr, int(p["plc_port"]),
                                                    p["plc_mode"])
            plc_default_cmd = "./{} {} {} {}".format(SYS_CONF["default_plc"], plc_addr, int(p["plc_port"]) + 2,
                                                     p["plc_mode"])
            logging.info("plc cmd res: {}".format(os.popen(plc_switch_cmd).read().strip()))
            logging.info("plc cmd res: {}".format(os.popen(plc_default_cmd).read().strip()))
        mongodb.plc.insert({"plc_addr": plc_addr, "plc_msg": plc_msg})
        self.publish(Cloud.topic_pub_plc_add, resp_data)

    def on_plc_del(self, data):
        """
        删除plc设备
        """
        plc_addr = data.get("plc_addr")
        mongodb.plc.delete_one({"plc_addr": plc_addr})
        resp_data = {
            "desc": "success",
        }
        if data.get("msg_id", None):
            resp_data["msg_id"] = data["msg_id"]
        self.publish(Cloud.topic_pub_plc_del, resp_data)

    def on_plc(self, data):
        """
        控制plc开关
        """
        plc_addr = data.get("plc_addr")
        plc_port = data.get("plc_port")
        plc_switch = data.get("plc_switch")
        plc_cmd = "./{} {} {} {}".format(SYS_CONF["default_plc"], plc_addr, plc_port, plc_switch)
        logging.info("plc cmd: {}".format(plc_cmd))
        logging.info("plc cmd res: {}".format(os.popen(plc_cmd).read().strip()))
        resp_data = {
            "desc": "success",
        }
        if data.get("msg_id", None):
            resp_data["msg_id"] = data["msg_id"]
        self.publish(Cloud.topic_pub_plc, resp_data)

    def on_plc_update(self, data):
        """
        设置plc端口信息
        """
        plc_addr = data.get("plc_addr")
        plc_msg = list(data.get("plc_msg"))
        resp_data = {
            "desc": "success",
        }
        if data.get("msg_id", None):
            resp_data["msg_id"] = data["msg_id"]
        mongodb.plc.update_one({"plc_addr": plc_addr}, {"$set": {"plc_msg": plc_msg}})
        self.publish(Cloud.topic_pub_plc_update, resp_data)

    def t_report_health(self):
        time.sleep(10)
        while True:
            self.report_health()
            time.sleep(60)

    def report_health(self):
        """
        心跳
        """
        eth0, mac, tun0 = psdctl.get_ip_info()
        mem, disk, cpu, status = evectl.get_psutil_info()
        data = {
            "mac": mac,  # mac地址
            "tun0": tun0,  # tun0 IP
            "eth0": eth0,  # eth0 IP
            "port": SYS_CONF["external_port"],  # http服务端口号
            "cpu": cpu,  # cpu占用率
            "mem": mem,  # 内存使用率
            "disk": disk,  # 磁盘使用率
            "device_status": status  # cpu/内存/磁盘/电量/流量等异常状态
        }
        logging.info("report_health data: {}".format(data))
        self.publish(Cloud.topic_pub_health, data)

    def report_event(self):
        """
        设备事件
        """
        time.sleep(10)
        while True:
            try:
                event = {"cpu": "CPU利用率", "mem": "内存利用率", "disk": "磁盘容量"}
                for k, v in event.items():
                    info, num = evectl.get_event_info(k, v)
                    data = {
                        "title": info,
                        "time": clkctl._unix13ts(),
                        "type": k,
                        "number": num,
                    }
                    if num >= 40:
                        logging.info("event info: {}".format(data))
                        self.publish(Cloud.topic_pub_event, data)
                time.sleep(1800)
            except Exception as err:
                logging.error(err)

    def report_setting(self, msg_id=None):
        """
        设备设置变更
        msg_id：如果收到的变更中包含msgId，传递；边侧自己修改则不需要传递
        """
        try:
            cam_info = camctl.get_rand_one()
        except Exception as e:
            logging.error(e)
            return

        data = {
            "interval": cam_info.interval,  # 采集间隔，5秒
            "detection_cycle": cam_info.detection_cycle,  # 采集时段设置
            "history": cam_info.history,  # 历史图片存储设置
            "alert": cam_info.alert,  # 告警图片存储设置
            "upload": cam_info.upload,
            "time": clkctl._unix13ts(),  # 时间戳
        }
        if msg_id:
            data["msg_id"] = msg_id
        self.publish(Cloud.topic_pub_setting, data)

    def report_date(self, msg, date, msg_id=None):
        """
        设备校时
        """
        data = {
            "desc": msg,
            "daytime": date
        }
        if msg_id:
            data["msg_id"] = msg_id
        logging.info("report date data: {}".format(data))
        self.publish(Cloud.topic_pub_time, data)

    def report_cam_setting(self, cam_uuid, msg_id=None):
        """
        普通摄像头设置变更
        msg_id：如果收到的变更中包含msgId，传递；边侧自己修改则不需要传递
        """
        cam_info = camctl.get_one(cam_uuid)
        data = {
            "interval": cam_info.interval,  # 采集间隔，5秒
            "detection_cycle": cam_info.detection_cycle,  # 采集时段设置
            "history": cam_info.history,  # 历史图片存储设置
            "alert": cam_info.alert,  # 告警图片存储设置
            "upload": cam_info.upload,

            "cam_uuid": cam_uuid,  # 摄像头编号，修改该摄像头设置
            "time": clkctl._unix13ts(),  # 时间戳
        }
        if msg_id:
            data["msg_id"] = msg_id
        self.publish(Cloud.topic_pub_cam_setting, data)

    def report_cam_del(self, cam_uuids):
        """
        边侧单独删除摄像头
        """
        if isinstance(cam_uuids, str):
            cam_uuids = [cam_uuids]

        data = {
            "cams": [{"uuid": cam_uuid} for cam_uuid in cam_uuids]
        }
        self.publish(Cloud.topic_pub_cam_del, data)

    def report_function(self, msg_id=None, device_id=None):
        """
        更新边侧设备告警设置

        需要边侧启动并连接成功后向云侧主动报告一次
        """
        data = {}
        if msg_id:
            data["msg_id"] = msg_id
        if device_id:
            data["function"] = camctl.get_one(device_id).function
        elif device.is_edge_proxy():
            data["function"] = functl.get("")
        else:
            cam = device.get_edge_ipc_cam()
            data["function"] = cam.function
        logging.info("report function: {}".format(data))
        self.publish(Cloud.topic_pub_function, data)

    def report_function_cam(self, device_ids, msg_id=None):
        """
        边侧更新某摄像头告警设置
        msg_id：如果收到的变更中包含msgId，传递；边侧自己修改则不需要传递
        """
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        data = {
            "cams": [{"functions": camctl.get_one(device_id).function, "device_id": device_id} for device_id in
                     device_ids],
            "time": clkctl._unix13ts()
        }
        if msg_id:
            data["msg_id"] = msg_id
        self.publish(Cloud.topic_pub_function_cam, data)

    def report_alert(self, data, cam_info, img_path):
        """
        边侧上传AI告警
        """
        if cam_info.upload and not cam_info.upload.get("alert_enable", True):
            logging.warning("no need to send alert to mqtt. camera alert upload not enable. cam uuid: %s",
                            cam_info.uuid)
            return

        with open(img_path, "rb") as f:
            data["img_str"] = str(base64.b64encode(f.read()), encoding='utf-8')

        self.publish(Cloud.topic_pub_alert, data)

    def report_img(self, device_id, save_name, img_path, timestamp, img_size, if_sto_db):
        """
        历史采集图片上传
        TODO: 1.当本地存储关闭后,云端存储打开,因为upload方式,所以并不会传图
              2.当sto_img 为false情况, 本地不保存图片, 只能设置为base64
        """
        cam_info = camctl.get_one(device_id)
        if not camctl.if_upload_img(cam_info):
           return

        data = {
            "name": save_name,
            "device_id": device_id,
            "create_time": timestamp,
            "size": img_size,
            # "path": img_path.split("local/")[1],
        }
        if cam_info.upload and cam_info.upload.get("img_type", "") == "local":
            if not if_sto_db:
                with open(img_path, "rb") as f:
                    data["img_str"] = str(base64.b64encode(f.read()), encoding="utf-8")
            else:
                data["path"] = img_path.split("w2s/")[1]
        else:
            logging.info("upload type: %s", cam_info.upload.get("img_type", ""))
            with open(img_path, "rb") as f:
                data["img_str"] = str(base64.b64encode(f.read()), encoding="utf-8")

        camctl.update_last_upload(device_id)
        self.publish(Cloud.topic_pub_img, data)

    def report_img_del(self, device_id, path_list):
        """
        历史采集图片删除
        path_list: [{"path": it["path"], "create_time": it["timestamp"] * 1000}
        """
        logging.info("device {}, delete img: {}".format(device_id, path_list))
        if not path_list:
            return

        data = [
            {
                "path": img_path["path"].split("w2s/")[1],
                "device_id": device_id,
                "create_time": img_path["timestamp"]
            } for img_path in path_list]
        self.publish(Cloud.topic_pub_img_del, data)

    def publish(self, topic, data, qos=2):
        if self.mqtt_client:
            try:
                # self.mqtt_client.publish(topic=topic, payload=json.dumps(data), qos=qos)
                publish.single(topic, json.dumps(data), qos, False, SYS_CONF["mqtt"]["addr"], SYS_CONF["mqtt"]["port"])
            except:
                logging.exception("mqtt publish fail. topic: %s", topic)


CldT = Cloud()
