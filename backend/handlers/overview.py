import os
import re
import logging

from backend.handlers.base import AsyncHandler
from backend.driver import camera as camctl
from backend.driver import bucket as bktctl
from backend.driver.mongo import mongodb, resize_mongo_result


class OverviewHandler(AsyncHandler):

    def _get_latest_images(self, camera, amount):
        #device_id = camera['uuid']
        #fetch = mongodb.images.find({"source": device_id}).sort("timestamp", -1).limit(amount)
        images = bktctl.latest_images(camera.uuid, amount)
        return {
            "device_id": camera.uuid,
            "device_name": camera.name,
            "location": camera.location,
            "function": camera.function,
            "items": [os.path.join("/media/{}/image".format(camera.uuid), img['name']) for img in images]
        }

    def do_get(self, data):
        limit = int(data.get("limit", 0))
        offset = int(data.get("offset", 0))
        search = data.get("search", None)
        location = data.get("location", None)

        query = {}
        if search is not None and search is not "":
            query["$or"] = [
                {'name': re.compile(re.escape(search))},
                {'uuid': re.compile(re.escape(search))},
                {'location': re.compile(re.escape(search))}
            ]
        if location:
            query["location"] = location

        #fetch = mongodb.device.find(query)
        #results = resize_mongo_result(fetch, limit=limit, offset=offset)
        #device_info = [self.get_latest_images(d.uuid, 3) for d in results]
        cameras, amount = camctl.get_all(query, limit=limit, offset=offset)
        device_info = [self._get_latest_images(cam, 3) for cam in cameras]

        return self.success({
            "data": device_info,
            "total_count": amount,
        })


class OverviewLocationHandler(AsyncHandler):
    def do_get(self, data):
        locations = set([cam.location for cam in camctl.get_all({})[0]])
        results = {}
        for l in locations:
            results[l] = l
        return self.success(results)
