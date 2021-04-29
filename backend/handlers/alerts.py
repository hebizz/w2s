import re
import json
import logging

from bson import ObjectId

from backend.handlers import base
from backend.driver import clock as clk
from backend.driver import alert as altctl
from backend.settings import SYS_CONF

class PageHandler(base.AsyncHandler):
    def do_get(self, data):
        pass
        try:
            return self.success()
        except Exception as err:
            logging.exception(err)
            return self.failed(500, "{}".format(err))

class AlertsHandler(base.AsyncHandler):
    def do_get(self, data):
        """ 获取告警 """
        search = data.get("search", None)
        offset = int(data.get("offset", 0))
        limit = int(data.get("limit", 0))
        time_from = int(data.get("from", 0))
        time_until = int(data.get("until", 0))
        status = data.get("status", None)
        title = data.get("title", None)
        device_id = data.get("device_id", None)
        alert_id = data.get("alert_id", None)

        query = {}
        if alert_id:
            query["_id"] = ObjectId(alert_id)
        if status:
            query["status"] = status
        if title:
            query["title"] = title  # {"$elemMatch": {"title": title}}
        if device_id:
            query["device_id"] = device_id
        if time_from and time_until:
            query["create_time"] = {'$lte': time_until, '$gte': time_from}

        if search:
            query["$or"] = [
                {'device_name': re.compile(re.escape(search))},
                {'device_id': re.compile(re.escape(search))}
            ]

        alert_list, count = altctl.get_all(query, limit=limit, offset=offset)
        alerts = [a.data for a in alert_list]
        # remove "img_url" from frontent
        for a in alerts:
            a['img_url'] = a['path']
        return self.success({
            "data": alerts,
            "total_count": count,
        })

    def do_put(self, data):
        """ 确认告警 """
        alert_id = data.get("alert_id", None)
        if alert_id is None:
            return self.failed(490, "not found alert id")

        alert = altctl.confirm(
            {"_id": ObjectId(alert_id)},
            self.userinfo.name,
            self.userinfo.user_id
        )
        return self.success(alert.data)

    def do_delete(self, data):
        """ 关闭告警 """
        alert_ids = data.get("alert_ids", None)
        if alert_ids is None:
            return self.failed(490, "not found alert id")
        try:
            alert_ids = json.loads(alert_ids)
        except Exception:
            return self.failed(491, "invalid alert id")

        alerts = altctl.close(
            {"_id": {"$in": [ObjectId(aid) for aid in alert_ids]}},
            self.userinfo.name,
            self.userinfo.user_id
        )
        return self.success([a.data for a in alerts])

class AlertsDeleteHandler(base.AsyncHandler):
    def do_delete(self, data):
        """ 删除告警 """
        alert_ids = data.get("alert_ids", None)
        if alert_ids is None:
            return self.failed(490, "not found alert_id")
        alert_ids = json.loads(alert_ids)

        query = {"_id": {"$in": [ObjectId(alert_id) for alert_id in alert_ids]}}
        altctl.delete(query)
        return self.success()

class AlertsSummaryHandler(base.AsyncHandler):
    def do_get(self, data):
        """报警数据统计"""
        time_from = int(data.get("from", 0))
        time_until = int(data.get("until", 0))
        status = data.get("status", None)
        title = data.get("title", None)

        query = {}
        if status:
            query["status"] = status
        if title:
            query["title"] = title
        if time_from and time_until:
            query["create_time"] = {'$lte': time_until, '$gte': time_from}

        alerts_count, open_alerts_count, alert_devices_count = altctl.summary(query)

        data = {
            "total_alerts_count": alerts_count,
            "open_alerts_count": open_alerts_count,
            "alert_devices_count": alert_devices_count
        }
        return self.success(data)

class RefreshHandler(base.AsyncHandler):
    def do_get(self, data):
        try:
            last_timestamp = int(data.get("timestamp", -1))
            if last_timestamp == -1:   # represent the first time fetching
                alerts = altctl.get_all({}, limit=SYS_CONF['alert_first_fetch'])[0]
            else:
                alerts = altctl.get_all({
                    "create_time": {'$gte': clk.d13to10(last_timestamp)}
                })[0]
            data = [a.data for a in alerts]
        except Exception as err:
            logging.exception(err)
            self.failed(500, "failed to refresh alert")
        return self.success({"data": data})

class AlertsSummaryStatusHandler(base.AsyncHandler):
    def do_get(self, data):
        time_from = int(data.get("from", 0))
        time_until = int(data.get("until", 0))
        title = data.get("title", None)
        device_id = data.get("device_id", None)

        query = {}
        if device_id:
            query["device_id"] = device_id
        if title:
            query["title"] = title
        if time_from and time_until:
            query["create_time"] = {'$lte': time_until, '$gte': time_from}

        close_alerts_count, open_alerts_count = altctl.summary_status(query)
        return self.success({
            "close_alerts_count": close_alerts_count,
            "open_alerts_count": open_alerts_count
        })

class AlertsSummaryCategoryHandler(base.AsyncHandler):
    def do_get(self, data):
        time_from = int(data.get("from", 0))
        time_until = int(data.get("until", 0))
        status = data.get("status", None)
        device_id = data.get("device_id", None)
        title = data.get("title", None)

        query = {}
        if device_id:
            query["device_id"] = device_id
        if title:
            query["title"] = title
        if status:
            query["status"] = status
        if time_from and time_until:
            query["create_time"] = {'$lte': time_until, '$gte': time_from}

        alert_sum_category = altctl.summary_category(query)

        return self.success(alert_sum_category)
