

class Face(object):

    def __init__(self, data):
        self._data = data

    def id(self):
        return str(self._data["_id"])

    @property
    def data(self):
        return self._data

    @property
    def name(self):
        return self._data["name"]

    @property
    def feature(self):
        return self._data["feature"]

    @property
    def faceid(self):
        return self._data["faceid"]
    