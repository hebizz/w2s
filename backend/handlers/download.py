import logging

from backend.settings import SYS_CONF
from backend.handlers import base
from backend.driver.excel import Write
from backend.driver import alert as altctl

class DownloadHandler(base.BaseHandler):

     async def get(self):
        data = self.parse_query_arguments()
        time_from = int(data.get('from'))
        time_until = int(self.get_argument('until'))
        title = data.get("title")
        status = data.get("status")
        device_id = data.get("device_id")
        logging.info("#####################{} {}".format(time_from, time_until))
        query = {}
        if device_id:
            query["device_id"] = device_id
        if title:
            query["title"] = title
        if status:
            query["status"] = status
        if time_from and time_until:
            query["create_time"] = {'$lte': time_until, '$gte': time_from}

        alerts = [a.data for a in altctl.get_all(query)[0]]
        alert_count = {}
        for alert in alerts:
            alert_title = alert.get("title", "undefined")
            if alert_title in alert_count:
                alert_count[alert_title] += 1
            else:
                alert_count[alert_title] = 1

        logging.info("#####################{} {}".format(time_from, time_until))
        excel = Write("alert", "alert").write_alert(time_from, time_until, alert_count, alerts)
        logging.info("##################### {}".format(excel))

        if not excel:
            self.write_error(500)
        await self.create_static_file_handler(excel.get('name'), excel.get('path'))
