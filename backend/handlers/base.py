# -*- coding: utf-8 -*-
import time
import json
import base64
import logging

import tornado.web
from tornado import iostream
from Crypto.Cipher import AES

from backend.settings import SYS_CONF
from backend.driver.acl import aclcore
from backend.model.userinfo import UserInfo, UserTicket


def encrypt(key, uid, timestamp):
    def uid2message(uid, timestamp):
        ret = "{}/{}/jx".format(uid, timestamp)
        aim_length = int(len(ret) / 16) * 16 + 16
        return ret + (" " * (aim_length - len(ret)))

    try:
        obj = AES.new(key, AES.MODE_CBC, 'default salt 16b')
        return obj.encrypt(uid2message(uid, timestamp))
    except TypeError:
        obj = AES.new(key.encode('utf-8'), AES.MODE_CBC, 'default salt 16b'.encode('utf-8'))
        return obj.encrypt(uid2message(uid, timestamp).encode('utf-8'))


def decrypt(key, message):
    def message2uid(text):
        if isinstance(text, bytes):
            text = str(text, encoding='utf-8')
        return tuple(text.strip().split("/"))

    try:
        obj = AES.new(key, AES.MODE_CBC, 'default salt 16b')
    except TypeError:
        obj = AES.new(key.encode('utf-8'), AES.MODE_CBC, 'default salt 16b'.encode('utf-8'))
    return message2uid(obj.decrypt(message))


def calc_ticket(uid, timestamp):
    key = SYS_CONF["cookie_secret"]
    return encrypt(key, uid, timestamp)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class BaseHandler(tornado.web.RequestHandler):

    def get(self):
        self.finish("hello world!")

    def get_current_uid(self):
        if SYS_CONF["debug"]:
            return SYS_CONF["debug_user"]
        return self.current_uid

    def set_current_uid(self):
        self.current_uid = None
        cookie = self.get_cookie(SYS_CONF["login_cookie"])
        if cookie is None:
            return None
        t = base64.b64decode(cookie)
        uid, timestmap, token = decrypt(SYS_CONF["cookie_secret"], t)
        if token != "jx":
            return False
        self.userinfo = UserInfo.get_user_by_id(uid)
        if not self.userinfo:
            self.clear_login_cookies()
            return None
        if self.userinfo.re_cookie:
            return False
        self.current_uid = uid
        return True

    def clear_login_cookies(self):
        self.clear_cookie(SYS_CONF["login_cookie"])

    def set_login_cookie(self, uid):
        now = int(time.time() * 1000)
        tickets = UserTicket.get_ticket(uid)
        if len(tickets) == 0:
            ticket = UserTicket.new_ticket({
                "uid": uid,
                "ticket": calc_ticket(uid, now),
                "timestamp": now,
            })
        else:
            ticket = tickets[0]
        self.set_cookie(SYS_CONF["login_cookie"], base64.b64encode(
            ticket.ticket), expires_days=3)

    def prepare(self):
        '''
           status_cookie:
            1.None 没有cookie
            2.True cookie有效
            3.False cookie失效
        '''
        if not SYS_CONF["debug"]:
            status_cookie = self.set_current_uid()
            url = self.request.path
            if status_cookie is None:
                if not aclcore.enforce("visitor", url, self.request.method):
                    return self.login_failed()
            else:
                if not status_cookie:
                    self.clear_login_cookies()
                    return self.login_failed()
                else:
                    if not aclcore.enforce(self.userinfo.role, url, self.request.method):
                        return self.access_failed()

    def parse_json(self, raw_data):
        if raw_data == b"":
            return {}
        if isinstance(raw_data, bytes):
            try:
                data = str(raw_data, encoding='utf-8')
            except:
                return {"data": str(base64.b64encode(raw_data), encoding='utf-8')}
        else:
            data = raw_data
        data = json.loads(data)
        return data

    def parse_json_body(self):
        try:
            self.request_data = self.parse_json(self.request.body)
        except (KeyError, ValueError) as e:
            self.write_error(500, "bad json format: {}".format(str(e)))
            self.request_data = None
        return self.request_data

    def parse_query_arguments(self):
        ret = {}
        for k, v in self.request.query_arguments.items():
            if isinstance(v, list) and len(v) != 0:
                if isinstance(v[0], bytes):
                    ret[k] = str(v[0], encoding='utf-8')
                else:
                    ret[k] = v[0]
            else:
                ret[k] = v
        return ret

    def finish_request(self, body):
        self.write(json.dumps(body, sort_keys=True, separators=(',', ': ')))
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.finish()

    def write_success_json(self, data=None):
        self.set_status(200)
        if data is None:
            return self.finish_request({"desc": "success", "data": ""})
        else:
            return self.finish_request({"desc": "success", "data": data})

    def login_failed(self):
        self.write_error(499, "bad login user: login failed")

    def access_failed(self):
        self.write_error(403, "you do not have permission to access this page")

    def write_error(self, status_code, desc=None, reason=None, **kwargs):
        result = {}
        if reason:
            self.set_status(status_code, reason=reason)
        else:
            self.set_status(status_code)

        if desc is None and "exc_info" in kwargs:
            desc = str(kwargs["exc_info"][1])

        result['desc'] = desc
        self.finish_request(result)

    async def create_static_file_handler(self, name, path):
        self.set_header("Content-Type", "application/octet-stream")
        self.set_header("Content-Disposition", "attachment; filename={}".format(name))
        content = tornado.web.StaticFileHandler.get_content(path)
        logging.info(content)
        if isinstance(content, bytes):
            content = [content]
        for chunk in content:
            try:
                self.write(chunk)
                await self.flush()
            except iostream.StreamClosedError:
                self.write_error(500, desc="download file failed, retry")
                return
        self.set_status(200)
        self.finish()


class AsyncHandler(BaseHandler):

    def success(self, result=None):
        return 200, result

    def failed(self, status_code, result=None):
        return status_code, result

    def write_success(self, result):
        return self.write_success_json(result)

    @property
    def executor(self):
        return self.application.executor

    @tornado.gen.coroutine
    def async_worker(self, func, data):
        status, result = yield self.executor.submit(func, (data))
        if status == 200:
            return self.write_success(result)
        else:
            return self.write_error(status, result)

    def do_post(self, data):
        return self.failed(404, "no implement")

    def do_put(self, data):
        return self.failed(404, "no implement")

    def do_get(self, data):
        return self.failed(404, "no implement")

    def do_delete(self, data):
        return self.failed(404, "no implement")

    def post(self):
        data = self.parse_json_body()
        return self.async_worker(self.do_post, data)

    def put(self):
        data = self.parse_json_body()
        return self.async_worker(self.do_put, data)

    def get(self):
        data = self.parse_query_arguments()
        return self.async_worker(self.do_get, data)

    def delete(self):
        data = self.parse_query_arguments()
        return self.async_worker(self.do_delete, data)
