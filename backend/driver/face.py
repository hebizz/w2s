import logging

from backend.model.face import Face
from backend.driver.mongo import mongodb, resize_mongo_result, mongo_id_to_str


def get_one(face_id):
    fetch = mongodb.facedata.find_one({"faceid": face_id})
    if fetch is None:
        raise RuntimeError("no such face ({}) in database".format(face_id))
    return Face(mongo_id_to_str(fetch))

def get_all(query, limit=0, offset=0):
    fetch = mongodb.facedata.find(query)
    if fetch is None:
        logging.warning("facedata-all (%s) returns empty", query)
        return [], 0
    results = resize_mongo_result(fetch, limit=limit, offset=offset)
    return [Face(mongo_id_to_str(r)) for r in results], fetch.count()

def add(name, faceid, feature):
    face_data = {
        "name": name,
        "faceid": faceid,
        "feature": feature,
    }
    upper_limit_num = 5
    for f in get_all({})[0]:    # take this structure to handle more complicated scenario
        if f.name == name:
            if len(f.feature) <= upper_limit_num:
                mongodb.facedata.insert_one(face_data)

def delete(faceid):
    mongodb.facedata.delete_one({"faceid": faceid})