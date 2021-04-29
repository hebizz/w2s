# -*- coding: UTF-8 -*-
import os
import logging
from ctypes import byref

from backend.driver import dylib
from backend.model.hiksdk import NET_DVR_USER_LOGIN_INFO, NET_DVR_DEVICEINFO_V40, NET_DVR_JPEGPARA


sdk = ['/usr/lib/libhcnetsdk.so']
BASE_DIR = "/data/tmpfs/hiksdk"
BASE_PATH = "/data/tmpfs/hiksdk/{}_capture.jpg"

def get_frame(address, username, password):
    _hik_sdk_capture(address, username, password)
    with open(BASE_PATH.format(address), 'rb') as f:
        frame = f.read()
    return frame

def _errmsg():
    return str(dylib.call(sdk, "NET_DVR_GetLastError"))

def _hik_sdk_capture(address, username, password, port=8000):
    logging.info("HikCam Capturing...")

    dylib.call(sdk, "NET_DVR_Init")
    logging.debug("NET_DVR_Init()")

    if not dylib.call(sdk, "NET_DVR_SetConnectTime", 5000, 5):
        raise RuntimeError("failed to set timeout")
    logging.debug("NET_DVR_SetConnectTime()")
    sDVRIP_bytes = bytes(address, "ascii")
    sUserName = bytes(username, "ascii")
    sPassword = bytes(password, "ascii")
    struLoginInfo = NET_DVR_USER_LOGIN_INFO()
    struLoginInfo.bUseAsynLogin = 0
    i = 0
    for o in sDVRIP_bytes:
        struLoginInfo.sDeviceAddress[i] = o
        i += 1
    struLoginInfo.wPort = port
    i = 0
    for o in sUserName:
        struLoginInfo.sUserName[i] = o
        i += 1
    i = 0
    for o in sPassword:
        struLoginInfo.sPassword[i] = o
        i += 1
    device_info = NET_DVR_DEVICEINFO_V40()
    loginInfo1 = byref(struLoginInfo)
    loginInfo2 = byref(device_info)
    lUserID = dylib.call(sdk, "NET_DVR_Login_V40", loginInfo1, loginInfo2)
    if lUserID == -1:
        logging.error("failed to login (%s): %s", address, _errmsg())
    logging.debug("log in (%s): %s", address, lUserID)

    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)
    cap_path = BASE_PATH.format(address)
    sJpegPicFileName = bytes(cap_path, "ascii")
    lpJpegPara = NET_DVR_JPEGPARA()
    lpJpegPara.wPicSize = 0
    lpJpegPara.wPicQuality = 1
    if dylib.call(sdk, "NET_DVR_CaptureJPEGPicture",
                  lUserID, 1, byref(lpJpegPara), sJpegPicFileName) == False:
        raise RuntimeError("failed to capture ({}): {}".format(address, _errmsg()))
    logging.debug("captured (%s)", address)

    if not dylib.call(sdk, "NET_DVR_Logout_V30", lUserID):
        raise RuntimeError("failed to log out ({}): {}".format(address, _errmsg()))
    logging.debug("log out (%s)", address)

    if dylib.call(sdk, "NET_DVR_Cleanup") < 0:
        raise RuntimeError("sdk resource release failed: {}".format(_errmsg()))
    logging.debug("sdk relase success")
    logging.info("HikCam Captured")
