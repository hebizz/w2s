# -*- coding: UTF-8 -*-
import os
import logging


BASE_DIR = "/var/w2s/tmpfs/rvisp"
BASE_PATH = "/var/w2s/tmpfs/rvisp/{}_capture.jpg"

def get_frame(rtsp_url, address):
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)
    cap_path = BASE_PATH.format(address)
    logging.info("require capture path: %s", cap_path)
    with open(cap_path, 'rb') as f:
        frame = f.read()
    return frame
