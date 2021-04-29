# coding: utf-8

from copy import deepcopy
from bson.objectid import ObjectId
import time


from backend.driver.mongo import mongodb, resize_mongo_result
from backend.model import MongoBase
from backend.model.misc import check_field
from backend.settings import SYS_CONF


class MongoUserInfoBase(MongoBase):

    def collection(self):
        return mongodb.userinfo()


class MongoUserInfo(MongoUserInfoBase):

    required_field = ["name", "password", "re_cookie", "user_id", "role", "remark", "reset", "create_time"]

    def __init__(self, data):
        self.data = deepcopy(data)
        check_field(data, MongoUserInfo.required_field)

    @property
    def id(self):
        return self.data["_id"]

    @property
    def user_id(self):
        return self.data["user_id"]

    @property
    def name(self):
        return self.data["name"]

    @property
    def password(self):
        return self.data["password"]

    @property
    def re_cookie(self):
        return self.data["re_cookie"]

    @property
    def user_no(self):
        return self.data["user_id"]

    @property
    def role(self):
        return self.data["role"]

    @property
    def remark(self):
        return self.data["remark"]

    @property
    def reset(self):
        return self.data["reset"]

    @property
    def create_time(self):
        return self.data["create_time"]

    @password.setter
    def password(self, new_value):
        self.data["password"] = new_value


class UserInfo(object):

    initialized = False
    @classmethod
    def create_admin_if_not_exist(cls):
        if not cls.initialized:
            if len(cls.get_admin_users()) == 0:
                cls.new_user({
                    "_id": ObjectId("5de620e696f0fd04c3836a3c"),
                    "name": SYS_CONF["admin"]["name"],
                    "password": SYS_CONF["admin"]["password"],
                    "re_cookie": False,
                    "user_id": 0,
                    "role": "admin",
                    "remark": "Super Administrator",
                    "reset": True,
                    "create_time": int(time.time())
                }).userinfo_save()

            cls.initialized = True

    @classmethod
    def create_id_by_role(cls, role):
        ret = mongodb.counters().find_one_and_update({"_id": "role-"+role}, {"$inc": {"next_id": 1}})
        nextid = ret["next_id"]
        return nextid

    @classmethod
    def create_user(cls, name, password, remark, role, reset):
        user_id = cls.create_id_by_role(role)
        cls.new_user({
            "name": name,
            "password": password,
            "re_cookie": False,
            "user_id": user_id,
            "role": role,
            "remark": remark,
            "reset": reset,
            "create_time" : int(time.time())
        }).save()

    @classmethod
    def new_user(cls, data):
        return MongoUserInfo(data)

    @classmethod
    def db_find(cls, query=None, sorted_by=None, limit=None, offset=None):
        userinfos = mongodb.userinfo().find(query)
        if sorted_by is not None:
            userinfos = userinfos.sort(sorted_by, -1) 
        total_count = userinfos.count()

        if limit is not None:
            userinfos = userinfos.limit(limit)
        if limit == 0:
            userinfos = []
        elif offset is not None:
            userinfos = userinfos.skip(offset)
        return userinfos, total_count

    @classmethod
    def get_users(cls, query=None, sorted_by=None, limit=None, offset=None):
        # if query is None or len(query) == 0:
        #     query = {"role":{"$ne":"admin"}}
        userinfos, total_count = cls.db_find(query=query, sorted_by=sorted_by, limit=limit, offset=offset)
        rst = []
        for r in userinfos:
            # if r['role'] == 'admin':
            #     break
            rst.append(MongoUserInfo(r))
        return rst, total_count

    @classmethod
    def get_auth_user(cls, query=None, sorted_by=None, limit=None, offset=None):
        userinfos, total_count = cls.db_find(query=query, sorted_by=sorted_by, limit=limit, offset=offset)
        return [MongoUserInfo(r) for r in userinfos], total_count

    @classmethod
    def update_one(cls, name, password=None, re_cookie=None, remark=None, role=None, reset=None):
        update  = {}
        if password is not None:
            update["password"] = password
            update["update_time"] = int(time.time())
        if re_cookie is not None:
            update["re_cookie"] = re_cookie
        if remark is not None:
            update['remark'] = remark
        if reset is not None:
            update['reset'] = reset
        if role is not None:
            user_id = cls.create_id_by_role(role)
            update['role'] = role
            update['user_id'] = user_id
        return mongodb.userinfo().update_one({"name":name},{"$set":update}, upsert=True)

    @classmethod
    def delete_one(cls, name):
        result = mongodb.userinfo().delete_one({"name": name})
        return True if result.deleted_count > 0 else False

    @classmethod
    def get_user_by_id(cls, uid):
        userinfos, total_count = cls.db_find(query={"_id": ObjectId(uid)})
        if total_count == 0:
            return None
        return MongoUserInfo(userinfos[0])

    @classmethod
    def is_exist_by_name(cls, name):
        result, total_count = cls.get_users(query={"name": name})
        return True if total_count is not 0 else False

    @classmethod
    def get_user_nums(cls, role=None):
        if role is not None:
            result, total_count = cls.get_users(query={"role": role})
        else:
            result, total_count = cls.get_users()
        return total_count

    @classmethod
    def get_admin_users(cls, query=None, limit=None, offset=None):
        if not query:
            query = {"role": "admin"}
        else:
            query["role"] = "admin"
        res = mongodb.userinfo().find(query)
        res = resize_mongo_result(res)
        return [MongoUserInfo(r) for r in res]


class MongoUserTicketBase(MongoBase):

    def collection(self):
        return mongodb.userticket()


class MongoUserTicket(MongoUserTicketBase):

    required_field = ["ticket", "uid", "timestamp"]

    def __init__(self, data):
        self.data = deepcopy(data)
        check_field(data, MongoUserTicket.required_field)

    @property
    def ticket(self):
        return self.data["ticket"]


class UserTicket(object):

    @classmethod
    def get_ticket(cls, uid):
        res = mongodb.userticket().find({"uid": uid})
        return [MongoUserTicket(r) for r in res]

    @classmethod
    def new_ticket(cls, data):
        return MongoUserTicket(data)
