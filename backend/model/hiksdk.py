# -*- coding: UTF-8 -*-
from ctypes import *
import ctypes

class NET_DVR_USER_LOGIN_INFO(Structure):
    _fields_ = [
        ("sDeviceAddress", c_byte * 129),
        ("byUseTransport", c_byte),
        ("wPort", c_uint16),
        ("sUserName", c_byte * 64),
        ("sPassword", c_byte * 64),
        ("bUseAsynLogin", c_bool),
        ("byProxyType", c_byte),
        ("byUseUTCTime", c_byte),
        ("byLoginMode", c_byte),
        ("byHttps", c_byte),
        ("iProxyID", c_long),
        ("byRes3", c_byte * 120),
    ]

# 设备参数结构体。
class NET_DVR_DEVICEINFO_V30(Structure):
    _fields_ = [
        ("sSerialNumber", c_byte * 48),
        ("byAlarmInPortNum", c_byte),
        ("byAlarmOutPortNum", c_byte),
        ("byDiskNum", c_byte),
        ("byDVRType", c_byte),
        ("byChanNum", c_byte),
        ("byStartChan", c_byte),
        ("byAudioChanNum", c_byte),
        ("byIPChanNum", c_byte),
        ("byZeroChanNum", c_byte),
        ("byMainProto", c_byte),
        ("bySubProto", c_byte),
        ("bySupport", c_byte),
        ("bySupport1", c_byte),
        ("bySupport2", c_byte),
        ("wDevType", c_uint16),
        ("bySupport3", c_byte),
        ("byMultiStreamProto", c_byte),
        ("byStartDChan", c_byte),
        ("byStartDTalkChan", c_byte),
        ("byHighDChanNum", c_byte),
        ("bySupport4", c_byte),
        ("byLanguageType", c_byte),
        ("byVoiceInChanNum", c_byte),
        ("byStartVoiceInChanNo", c_byte),
        ("byRes3", c_byte * 2),
        ("byMirrorChanNum", c_byte),
        ("wStartMirrorChanNo", c_uint16),
        ("byRes2", c_byte * 2)]

class NET_DVR_DEVICEINFO_V40(Structure):
    _fields_ = [
        ("struDeviceV30", NET_DVR_DEVICEINFO_V30),
        ("bySupportLock", c_byte),
        ("byRetryLoginTime", c_byte),
        ("byPasswordLevel", c_byte),
        ("byProxyType", c_byte),
        ("dwSurplusLockTime", c_ulong),
        ("byCharEncodeType", c_byte),
        ("bySupportDev5", c_byte),
        ("byLoginMode", c_byte),
        ("byRes2", c_byte * 253),
    ]

class NET_DVR_Login_V40(Structure):
    _fields_ = [
        ("pLoginInfo", NET_DVR_USER_LOGIN_INFO),
        ("lpDeviceInfo", NET_DVR_DEVICEINFO_V40)
    ]

class NET_DVR_JPEGPARA(ctypes.Structure):
    _fields_ = [
        ("wPicSize", ctypes.c_ushort), # WORD
        ("wPicQuality", ctypes.c_ushort)] # WORDclass NET_DVR_USER_LOGIN_INFO(Structure):
