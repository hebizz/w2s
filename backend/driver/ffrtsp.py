# -*- coding: UTF-8 -*-
import os
import logging
import subprocess
import time
#import multiprocessing

#import cv2


BASE_DIR = "/data/tmpfs/ffrtsp"
BASE_PATH = "/data/tmpfs/ffrtsp/{}_{}_{}_capture.jpg"

## -y: overwrite the output image
CAPTURE_BASE_CMD = 'ffmpeg -rtsp_transport tcp -y -i {} -vframes 1 {}'

def get_frame(rtsp_url, address, channel):
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)
    cap_path = BASE_PATH.format(address, channel, int(time.time()*1000))
    capture_cmd = CAPTURE_BASE_CMD.format(rtsp_url, cap_path)
    logging.info("gen capture command: %s", capture_cmd)
    subprocess.call(capture_cmd.split(' '), shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(cap_path, 'rb') as f:
        frame = f.read()
    
    os.remove(cap_path)
    return frame
