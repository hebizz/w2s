from backend.handlers import base
from backend.model import translate
from backend.model.userinfo import UserInfo


class LoginHandler(base.AsyncHandler):

    def do_post(self, data):
        UserInfo.create_admin_if_not_exist()
        name = data.get("username", None)
        if not name:
            return self.failed(400, "username not found")
        password = data.get("password", None)
        if not password:
            return self.failed(400, "password not found")
        userinfos, total_count = UserInfo.get_auth_user(query={"name": name})
        if total_count == 0:
            return self.failed(404, "user not found")
        if total_count > 1:
            return self.failed(502, "too many users found")
        userinfo = userinfos[0]
        if userinfo.password != password:
            return self.failed(403, "invalid password")
        self.set_login_cookie(userinfo.id)
        UserInfo.update_one(name=name, re_cookie=False)
        return self.success(result=translate(userinfo))


class LogoutHandler(base.AsyncHandler):

    def do_post(self, data):
        uid = self.get_current_uid()
        userinfo = UserInfo.get_user_by_id(uid)
        name = userinfo.name
        self.clear_login_cookies()
        return self.success()
