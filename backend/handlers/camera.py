import re
import json
import logging

from backend.handlers import base
from backend.model.alert import Alert
from backend.model.image import Image
from backend.driver import alert as altctl
from backend.driver import camera as camctl
from backend.driver import bucket as bktctl
from backend.driver.mongo import mongodb, mongo_id_to_str
from backend.driver import poseidon
from backend.settings import SYS_CONF


class CameraHandler(base.AsyncHandler):
    def do_get(self, data):
        """ fetch cameras with query """
        search = data.get("search", None)
        offset = int(data.get("offset", 0))
        limit = int(data.get("limit", 0))
        device_id = data.get("device_id")
        try:
            query = {}
            if search is not None and search is not "":
                query["$or"] = [{'name': re.compile(re.escape(search))},
                                {'uuid': re.compile(re.escape(search))},
                                {'location': re.compile(re.escape(search))}]
            if device_id is not None:
                query["uuid"] = device_id

            cameras, amount = camctl.get_all(query, limit=limit, offset=offset)
            data = []
            for cam in cameras:
                _d = cam.data
                data.append(_d)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))
        return self.success({
            "data": data,
            "total_count": amount,
        })

    def do_put(self, data):
        """ start streaming on camera """ 
        device_id = data.get("device_id")
        try:
            cam = camctl.get_one(device_id)
            cam.open_stream()
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "failed to start streaming on {}".format(device_id))
        return self.success({'stream': cam.preview_stream()})

    def do_post(self, data):
        """ update camera basic information """
        device_id = data.get("device_id")
        try:
            name = data.get("name")
            if name is not None:
                camctl.update(device_id, {'name': name})
            location = data.get("location")
            if location is not None:
                camctl.update(device_id, {"location": location})
            interval = data.get("interval")
            if location is not None:
                camctl.update(device_id, {"interval": interval})
            cam = camctl.get_one(device_id)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))
        return self.success(cam.data)

    def do_delete(self, data):
        """ stop streaming on camera """
        device_id = data.get("device_id")
        try:
            cam = camctl.get_one(device_id)
            cam.close_stream()
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "failed to stop streaming on {}".format(device_id))
        return self.success({})

class CameraSummaryHandler(base.AsyncHandler):
    def do_get(self, data):
        cameras = camctl.get_all({})[0]
        normal_devices = 0
        abnormal_devices = 0
        for cam in cameras:
            if cam.status == "normal":
                normal_devices = normal_devices+1
            else:
                abnormal_devices = abnormal_devices+1
        summary = {
            "total_devices_count": normal_devices + abnormal_devices,
            "normal_devices_count": normal_devices,
            "abnormal_devices_count": abnormal_devices
        }
        return self.success(summary)

class CameraHistoryHandler(base.AsyncHandler):
    def do_get(self, data):
        device_id = data.get("device_id", None)
        time_from = int(data.get("from", 0))
        time_until = int(data.get("until", 0))
        offset = int(data.get("offset", 0))
        limit = int(data.get("limit", 0))
        alert_images_only = int(data.get("isalert", 0))
        if device_id is None:
            self.failed(490, "not found device_id")

        fetch0 = mongodb.images.find({
            'source': device_id,
            'timestamp': {'$lte': time_until, '$gte': time_from},
        }).sort('timestamp', -1)
        images_pathref = {}
        for it in fetch0:
            images_pathref[it.get('path').split('w2s/')[1]] = Image(mongo_id_to_str(it))

        fetch1 = mongodb.alerts.find({
            'device_id': device_id,
            'create_time': {'$lte': time_until, '$gte': time_from},
        }).sort('create_time', -1)
        alerts_pathref = {}
        for it in fetch1:
            alerts_pathref[it.get('path')] = Alert(mongo_id_to_str(it))

        final_list = []
        if alert_images_only:
            for im_path, _ in images_pathref.items():
                if im_path in alerts_pathref:
                    final_list.append({im_path: {
                        'alert_position': alerts_pathref[im_path].alert_position,
                    }})
        else:
            for im_path, _ in images_pathref.items():
                # TODO: move to new interface later
                final_list.append(im_path)

        return self.success({
            "data": final_list[offset:offset+limit],
            "total_count": len(final_list),
        })

    def do_delete(self, data):
        img_ids = data.get("img_ids")
        img_ids = json.loads(img_ids)

        # delete alerts of images
        query = {"img_url": {"$in": [img_id for img_id in img_ids]}}
        altctl.delete(query)

        # delete images
        bktctl.delete_many(img_ids)
        return self.success()

class CameraManagementHandler(base.AsyncHandler):
    def do_get(self, data):
        try:
            cameras = camctl.get_all({})[0]
            data = [cam.data for cam in cameras]
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "failed to list camera")
        return self.success(data)

    def do_post(self, data):
        """ add camera """
        camera_type = data.get("type")
        address = data.get("ip")
        username = data.get("username", "admin")
        password = data.get("password", "123456")

        if not camera_type or not address:
            return self.failed(500, "not found new camera input")

        try:
            if SYS_CONF["device"] != "ZL203":
                camctl.add(camera_type, address, username, password, cam_uuid=poseidon.get_poseidon_id())
            else:
                camctl.add(camera_type, address, username, password)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "failed to add camera")
        return self.success()

    def do_delete(self, data):
        """ delete camera """
        camera_uuid = data.get("uuid")
        if not camera_uuid:
            return self.failed(500, "not found new camera input")

        try:
            camctl.delete(camera_uuid)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "failed to delete camera")
        return self.success()

class FlavourHandler(base.AsyncHandler):
    def do_put(self, data):
        device_id = data.get("device_id")
        flavour = data.get("flavour", False)
        try:
            if flavour is True:
                camctl.update(device_id, {"flavour": True})
            else:
                camctl.update(device_id, {"flavour": False})
            cam = camctl.get_one(device_id)
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "failed to alter flavour")
        return self.success(cam.data)
