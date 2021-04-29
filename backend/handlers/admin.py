import logging
import json
import re

from backend.handlers import base
from backend.model import translate
from backend.model.userinfo import UserInfo


class Handler(base.AsyncHandler):

    def do_get(self, data):
        search = data.get("search", None)
        role = data.get("role", None)
        offset = int(data.get("offset", 0))
        limit = int(data.get("limit", 10))
        query = {}
        if search is not None and search is not "":
            query["$or"] = [{'name': re.compile(re.escape(search))},
                            {'user_id': int(search) if search.isdigit() else None}]
        if role is not None and role is not "":
            query["role"] = role
        userinfos, total_count = UserInfo.get_users(
            query=query, limit=limit, offset=offset, sorted_by="create_time")
        tup = []
        for userinfo in userinfos:
            data = translate(userinfo)
            tup.append(data)

        userNum = {
            "all_num": UserInfo.get_user_nums(),
            "viewer_num": UserInfo.get_user_nums("viewer"),
            "operator_num": UserInfo.get_user_nums("operator"),
            "developer_num": UserInfo.get_user_nums("developer")
        }
        result = [{"userNum": userNum}, {
            "total_count": total_count, "userinfo": tup}]
        return self.success(result=result)

    def do_post(self, data):
        userInfos = data.get("userInfos", None)
        for userinfo in userInfos:
            name = userinfo["name"]
            if UserInfo.is_exist_by_name(name):
                return self.failed(406, "{} already exists".format(name))
            else:
                UserInfo.create_user(name=name, password=userinfo["password"],
                                     remark=userinfo["remark"], role=userinfo["role"], reset=userinfo["reset"])
        return self.success()

    def do_put(self, data):
        patch = data.get("patch", None)
        userinfo = data.get("userinfo", None)
        if patch is not None:
            for name in patch['name']:
                UserInfo.update_one(name=name, role=patch["role"])
        if userinfo is not None:
            name = userinfo["name"]
            password = userinfo["password"] if userinfo["password"] is not None else None
            remark = userinfo["remark"] if userinfo["remark"] is not None else None
            role = userinfo["role"] if userinfo["role"] is not None else None
            UserInfo.update_one(name=name, password=password, remark=remark, role=role)
        return self.success()

    def do_delete(self, data):
        data = data.get("name", None)
        try:
            names = json.loads(data)
            for name in names:
                result = UserInfo.delete_one(name)
        except:
            return self.failed(400, "name is an array")
        return self.success() if result else self.failed(404, "Invalid user name")
