# coding: utf-8
from bson.objectid import ObjectId
from backend.misc.dict import merge
from backend.driver.mongo import mongo_id_to_str


class MongoBase():
    def __init__(self, data):
        self.data = None

    @property
    def id(self):
        return str(self.data["_id"])

    def collection(self):
        return None

    def prepare_save(self):
        pass

    def save(self):
        self.prepare_save()
        if "_id" in self.data:
            self.collection().replace_one({"_id": self.data["_id"]}, self.data)
        else:
            self.collection().insert_one(self.data)
        return self

    def userinfo_save(self):
        self.prepare_save()
        self.collection().insert_one(self.data)

    def prepare_delete(self):
        pass

    def delete(self):
        self.prepare_delete()
        self.collection().delete_one({"_id": ObjectId(self.data["_id"])})

    def prepare_update(self, data):
        pass

    def update(self, data, overwrite=True):
        self.prepare_update(data)
        merge(data, self.data)
        if overwrite:
            self.save()
        else:
            self.collection().update(
                {"_id": ObjectId(self.data["_id"])}, {"$set": data})


def translate(data):
    if isinstance(data, list):
        res = []
        for i in data:
            res.append(translate(i))
        return res
    elif isinstance(data, dict):
        res = {}
        for i, v in data.items():
            res[i] = translate(v)
        return res
    elif isinstance(data, MongoBase):
        return mongo_id_to_str(data.data)
    else:
        return data
