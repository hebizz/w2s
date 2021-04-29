

class Image(object):

    def __init__(self, data):
        self._data = data

    @property
    def data(self):
        return self._data

    @property
    def name(self):
        return self._data["name"]

    @property
    def path(self):
        return self._data["path"]

    @property
    def source(self):
        return self._data["source"]

    @property
    def timestamp(self):
        return self._data["timestamp"]
