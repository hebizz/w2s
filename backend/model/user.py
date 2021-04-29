class User(object):

    def __init__(self, data):
        pass

    def id(self):
        return self._data["id"]

    def name(self):
        return self._data["name"]

    def perms(self):
        return self._data["perms"]

    def create_timestamp(self):
        return self._data["create_timestamp"]

    def last_update_timestamp(self):
        return self._data["last_update_timestamp"]

    def data(self):
        return self._data["data"]


class UserPermsTableObj(object):

    def __init__(object):
        pass

    def reload(self):
        pass

    def readable(self, data):
        pass

    def writeable(self, data):
        pass


class UsersManagementObj(object):

    def __init__(self):
        pass

    def get_session_user(self, data):
        pass

    def check_user_perms(self, data, perms):
        pass

    def create_user(self, data):
        pass

    def delete_user(self, data):
        pass

    def update_user(self, data):
        pass

    def summary(self, data):
        pass


UsersManagement = UsersManagementObj()
UserPermsTable = UserPermsTableObj()
