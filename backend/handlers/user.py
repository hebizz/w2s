import logging

from backend.handlers import base
from backend.model import translate
from backend.model.userinfo import UserInfo


class Handler(base.AsyncHandler):

    def do_get(self, data):
        uid = data.get("uid", None)
        if uid is None:
            uid = self.get_current_uid()
        if uid is None:
            return self.failed(499, "this is a visitor, no user information")
        userinfo = UserInfo.get_user_by_id(uid)
        return self.success(result=translate(userinfo))

    def do_put(self, data):
        uid = self.get_current_uid()
        userinfo = UserInfo.get_user_by_id(uid)
        name = userinfo.name
        password = data.get("password", None)
        logging.info(password)
        UserInfo.update_one(name=name, password=password,
                            reset=False, re_cookie=True)
        self.clear_login_cookies()
        return self.success()
