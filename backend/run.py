#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import logging
import sys

import tornado
import tornado.web
import tornado.ioloop
import tornado.concurrent
from tornado.options import options

from .urls import url_patterns
from .settings import SYS_CONF
from backend.task import RT, CldT, PC
from backend.task.sweeper import Sweeper
from backend.driver import bucket as bktctl
from backend.middle import Middle

Middle.initialize(RT, CldT)


class TornadoApplication(tornado.web.Application):
    def __init__(self):
        tornado.web.Application.__init__(self, url_patterns, **SYS_CONF)
        self.executor = tornado.concurrent.futures.ThreadPoolExecutor(16)


def main():
    tornado.options.parse_command_line()

    setup_logging()

    # give up signal.SIGCHLD
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    # clean history
    if SYS_CONF.get("clean_history", False):
        bktctl.clean_history()

    # sweeper
    s = Sweeper()
    s.start()

    # routine
    RT.start()

    # webConfig
    PC.start()

    # mqtt
    CldT.start()

    app = TornadoApplication()
    app.listen(options.port)
    logging.info("start service at: {}".format(options.port))
    try:
        tornado.ioloop.IOLoop.current().start()
        logging.info("stop service")
    finally:
        logging.info("stop service")


def setup_logging_to_stream(stream, log_level):
    logger = logging.getLogger()
    channel = logging.StreamHandler(stream)
    channel.setLevel(log_level)
    channel.setFormatter(tornado.log.LogFormatter())
    logger.addHandler(channel)


def setup_logging(log_level=None):
    if log_level is None:
        log_level = getattr(logging, options.logging.upper())
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(log_level)
    setup_logging_to_stream(stream=sys.stdout, log_level=log_level)
