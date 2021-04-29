import os
import logging
import platform
import subprocess

from PIL import Image
from backend.driver import ffrtsp
from backend.driver import hiksdk
from backend.driver import rvisp
from backend.settings import SYS_CONF
from backend.model import device
from backend.driver import poseidon as psdctl

IPC_RTSP_PATTERN = {
    'xm_rtsp': 'rtsp://{address}:{port}/user={username}&password=&channel=1&stream=1.sdp?',  # isp camera
    'hik_rtsp': 'rtsp://{username}:{passwd}@{address}:{port}/h264/ch{channel}/{subtype}/av_stream',  # hikvision
    'hua_rtsp': 'rtsp://{username}:{passwd}@{address}:{port}/cam/realmonitor?channel={channel}&subtype=1',
    # dahua subtype=0(main stream)
    'uni_rtsp': 'rtsp://{username}:{passwd}@{address}:{port}/video2',  # uniview video1(main stream)
    'hik_nvr_rtsp': 'rtsp://{username}:{passwd}@{address}:{port}/Streaming/Channels/{channel}02'
}

IPC_RTSP_BACK_PATTERN = {
    'hik_nvr_rtsp': 'rtsp://{username}:{passwd}@{address}:{port}/Streaming/tracks/{channel}01?starttime={starttime}&endtime={endtime}'
}

FORWARD_PATTERN = 'ffmpeg -rtsp_transport tcp -i {} -vcodec copy -an -f flv {}'

FLV_STREAM_PATTERN = "http://{}:{}/live/{}"


class StreamMgr():
    """
    管理直播或回播句柄

    TODO: 目前关掉了计数，多路播放同一个摄像头互相之间会有影响
    """

    def __init__(self, name):
        self._name = name
        self._streams = {}  # 存储一个摄像头直播或回播路数和推送子进程 {uuid: [路数, subpid]}

    def add_stream(self, uuid, subpid=None):
        if uuid not in self._streams:
            self._streams[uuid] = [1, subpid]
            logging.info("{}: new open streaming for {}".format(self._name, uuid))
        # else:
        #     self._streams[uuid][0] += 1
        #     logging.info("{}: add record open streaming multi for {} to {}".format(self._name, uuid, self._streams[uuid][0]))

    def del_stream(self, uuid):
        if uuid not in self._streams:
            return

        # self._streams[uuid][0] -= 1  # 先把播放路数减一
        # logging.info("{}: del record open streaming multi for {} to {}".format(self._name, uuid, self._streams[uuid][0]))

        # # 如果没有其他路在播放，关掉视频推送子进程
        # if self._streams[uuid][0] <= 0:
        logging.info("{}: close streaming for {}".format(self._name, uuid))
        stream_subpid = self._streams[uuid][1]
        if stream_subpid is not None and stream_subpid.poll() == None:
            stream_subpid.kill()
        self._streams.pop(uuid)

    def is_open(self, uuid):
        if uuid not in self._streams:
            return False

        stream_subpid = self._streams[uuid][1]
        if stream_subpid is not None and stream_subpid.poll() == None:
            return True

        return False


online_stream_mgr = StreamMgr("online")
back_stream_mgr = StreamMgr("back")


class Camera():
    def __init__(self, data):
        self._data = data

    @property
    def data(self):
        return self._data

    @property
    def uuid(self):
        return self._data["uuid"]

    @property
    def name(self):
        return self._data["name"]

    @property
    def edgex_name(self):
        return self._data.get("edgex_name", self._data["name"])

    @property
    def location(self):
        return self._data["location"]

    @property
    def status(self):
        return self._data["status"]

    @property
    def wakeup_time(self):
        return self._data["wakeup_time"]

    @property
    def host_id(self):
        return self._data["host_id"]

    @property
    def host_ip(self):
        return self._data["host_ip"]

    @property
    def cam_type(self):
        return self._data["cam_type"]

    @property
    def cam_address(self):
        return self._data["cam_address"]

    @property
    def cam_port(self):
        return self._data["cam_port"]

    @property
    def cam_username(self):
        return self._data["cam_username"]

    @property
    def cam_passwd(self):
        return self._data["cam_passwd"]

    @property
    def cam_channel(self):
        return self._data["cam_channel"]

    @property
    def interval(self):
        return self._data.get("interval", SYS_CONF.get("default_capture_interval", 10))

    @property
    def function(self):
        return self._data.get("function", {})

    @property
    def detection_cycle(self):
        return self._data.get("detection_cycle", SYS_CONF.get("detection_cycle", {}))

    @property
    def history(self):
        return self._data.get("history", SYS_CONF.get("history", {}))

    @property
    def alert(self):
        return self._data.get("alert", SYS_CONF.get("alert", {}))

    @property
    def upload(self):
        return self._data.get("upload", SYS_CONF.get("upload", {}))

    @property
    def detected_times(self):
        return self._data["detected_times"]

    def frame(self):
        frm = None
        if self.cam_type in ("hua_rtsp", "hik_rtsp", "uni_rtsp", "hik_nvr_rtsp"):
            frm = ffrtsp.get_frame(self.stream(), self.cam_address, self.cam_channel)
        if self.cam_type == "xm_rtsp":
            frm = rvisp.get_frame(self.stream(), self.cam_address)
        if self.cam_type == "hik_sdk":
            if platform.machine().split("_")[0] != "x86":
                raise RuntimeError("hik sdk only support x86 architecture")
            frm = hiksdk.get_frame(self.cam_address, self.cam_username, self.cam_passwd)
        if device.is_edge_ipc():
            # 拿图前判断图片是否完整
            while True:
                try:
                    Image.open(SYS_CONF["TD201_capture_path"]).load()
                    break
                except Exception as err:
                    logging.exception(err)
                    logging.exception("picture is not valid")
            with open(SYS_CONF["TD201_capture_path"], 'rb') as f:
                frm = f.read()

        if frm is None:
            raise RuntimeError("failed captured on camera {}({})".format(self.uuid, self.cam_address))
        return frm

    def stream(self):
        return IPC_RTSP_PATTERN[self.cam_type].format(
            username=self.cam_username,
            passwd=self.cam_passwd,
            address=self.cam_address,
            port=self.cam_port,
            channel=self.cam_channel,
            subtype=SYS_CONF["hk_subtype"],
        )

    def back_stream(self, starttime, endtime):
        return IPC_RTSP_BACK_PATTERN[self.cam_type].format(
            username=self.cam_username,
            passwd=self.cam_passwd,
            address=self.cam_address,
            port=self.cam_port,
            channel=self.cam_channel,
            starttime=starttime,
            endtime=endtime
        )

    def forward_stream(self, back=False):
        forward_address = SYS_CONF['stream'].get('push', "127.0.0.1")
        suffix = self.uuid[:6]
        if back:
            suffix = "back-" + self.uuid[:6]
        return "rtmp://{}:1935/live/{}".format(forward_address, suffix)

    def preview_stream(self, back=False):
        preview_address = psdctl.get_host_ip()
        flv_port = SYS_CONF["stream"].get("flv_port", None)
        logging.info("preview address: %s:%s", preview_address, flv_port)
        suffix = self.uuid[:6]
        if back:
            suffix = "back-" + self.uuid[:6]
        if flv_port is None:
            # 支持旧的rtmp格式输出
            return "rtmp://{}:1935/live/{}".format(preview_address, suffix)
        # 使用http://gitlab.jiangxingai.com/wadewang/nstream作为流媒体服务器，可以直接输出HTTP FLV播放
        return FLV_STREAM_PATTERN.format(preview_address, flv_port, suffix)

    def open_stream(self):
        if online_stream_mgr.is_open(self.uuid):
            online_stream_mgr.add_stream(self.uuid)
            return

        if device.is_edge_proxy():
            stream_cmd = FORWARD_PATTERN.format(self.stream(), self.forward_stream())
            logging.info("gen stream command: {}".format(stream_cmd))
            online_stream = subprocess.Popen(stream_cmd.split(' '), shell=False)
            online_stream_mgr.add_stream(self.uuid, online_stream)
        else:
            preview_address = SYS_CONF['stream'].get('push', "127.0.0.1")
            stream_cmd = FORWARD_PATTERN.format("rtsp://{}/0".format(preview_address), self.forward_stream())
            logging.info("td201 gen stream command: {}".format(stream_cmd))
            online_stream = subprocess.Popen(stream_cmd.split(' '), shell=False)
            online_stream_mgr.add_stream(self.uuid, online_stream)

    def close_stream(self):
        online_stream_mgr.del_stream(self.uuid)

    def open_back_stream(self, starttime, endtime):
        if self.cam_type not in IPC_RTSP_BACK_PATTERN:
            raise Exception("该摄像头不支持回放")

        if back_stream_mgr.is_open(self.uuid):
            back_stream_mgr.add_stream(self.uuid)
            return

        stream_cmd = FORWARD_PATTERN.format(self.back_stream(starttime, endtime), self.forward_stream(back=True))
        logging.info("gen back stream command: {}".format(stream_cmd))
        back_stream = subprocess.Popen(stream_cmd.split(' '), shell=False)
        back_stream_mgr.add_stream(self.uuid, back_stream)

    def close_back_stream(self):
        back_stream_mgr.del_stream(self.uuid)
