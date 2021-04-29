

class Alert(object):

    def __init__(self, data):
        self._data = data

    def id(self):
        return str(self._data["_id"])

    @property
    def data(self):
        return self._data

    def path(self):
        return self._data["path"]

    def sub_type(self):
        return self._data["sub_type"]

    def device_id(self):
        return self._data["device_id"]

    def device_name(self):
        return self._data["device_name"]

    def host_id(self):
        return self._data["host_id"]

    def host_ip(self):
        return self._data["host_ip"]

    def title(self):
        return self._data["title"]

    @property
    def alert_position(self):
        return self._data["alert_position"]

    def create_time(self):
        return self._data["create_time"]

    def location(self):
        return self._data["location"]

    def status(self):
        return self._data["status"]

    def affirmed(self):
        return self._data["affirmed"]

