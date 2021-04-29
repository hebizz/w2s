import copy

import pymongo
from bson.objectid import ObjectId

from backend.settings import SYS_CONF
from backend.driver import memory

class MongoCore(object):

    def __init__(self):
        conf = SYS_CONF["mongodb"]
        self.db_adapter = pymongo.MongoClient(conf["addr"])[conf["db"]]
        self.db_adapter.counters.update(
            {"_id": "role-viewer"}, {"$setOnInsert": {"next_id": 1000001}}, upsert=True)
        self.db_adapter.counters.update(
            {"_id": "role-operator"}, {"$setOnInsert": {"next_id": 2000001}}, upsert=True)
        self.db_adapter.counters.update(
            {"_id": "role-developer"}, {"$setOnInsert": {"next_id": 3000001}}, upsert=True)

        # self.db_adapter.alerts.create_index(
        #     [("ttl", pymongo.ASCENDING)], expireAfterSeconds=2419200)

        function_table = SYS_CONF.get("function", {})
        self.db_adapter.function.update({}, {"$setOnInsert": function_table}, upsert=True)

        face_table = SYS_CONF.get("facedata", {})
        self.db_adapter.facedata.update({}, {"$setOnInsert": face_table}, upsert=True)

        # if SYS_CONF["device"] != "TD201":
            # pointer = SYS_CONF.get("chip_pointer", {})
            # self.db_adapter.pointer.update({}, {"$setOnInsert": pointer}, upsert=True)
            # tmp_pointer = self.db_adapter.pointer.find_one()
            # tmp_pointer.pop("_id")
            # memory.CHIP_POINTER_TABLE = tmp_pointer

        tmp_function = self.db_adapter.function.find_one()
        tmp_function.pop("_id")
        memory.FUNCTION_TABLE = tmp_function
        self.db_adapter.images.create_index([('source',1), ('timestamp',-1)])

        wanrning_count = {}
        tmp_device = self.db_adapter.device.find()
        tmp_devices = [mongo_id_to_str(r) for r in tmp_device]
        for device in tmp_devices:
            wanrning_count.update({device['uuid']: {func:[] for func in device["function"].keys()}})
        memory.WARNING_COUNT = wanrning_count


    @property
    def alerts(self):
        return self.db_adapter.alerts

    @property
    def images(self):
        return self.db_adapter.images

    @property
    def device(self):
        return self.db_adapter.device

    @property
    def function(self):
        return self.db_adapter.function

    @property
    def facedata(self):
        return self.db_adapter.facedata

    @property
    def pointer(self):
        return self.db_adapter.pointer

    @property
    def alert_management(self):
        return self.db_adapter.alert_management

    @property
    def alert_aggregation(self):
        return self.db_adapter.alert_aggregation

    @property
    def api_user(self):
        return self.db_adapter.api_user

    @property
    def plc(self):
        return self.db_adapter.plc

    def userinfo(self):
        return self.db_adapter.userinfo

    def userticket(self):
        return self.db_adapter.userticket

    def counters(self):
        return self.db_adapter.counters

def mongo_id_to_str(mgo_obj):
    """
        Transforms _id from mongo to what client accepts.
    """
    new_obj = copy.deepcopy(mgo_obj)
    # new_obj.pop("ttl", None)
    i = new_obj.pop("_id", None)
    if i:
        new_obj["id"] = str(i)
    uuid = new_obj.get("uuid", None)
    if uuid:
        new_obj["id"] = str(uuid)
    return new_obj

def str_id_to_mongo_id(str_obj):
    """
        Transforms _id from mongo to what client accepts.
    """
    mgo_obj = copy.deepcopy(str_obj)
    i = mgo_obj.pop("id", None)
    if i:
        mgo_obj["_id"] = ObjectId(i)
    return mgo_obj

def resize_mongo_result(result, limit=0, offset=0):
    if limit > 0:
        result = result.limit(limit)
    if offset > 0:
        result = result.skip(offset)
    return result

mongodb = MongoCore()
