import casbin

from backend.settings import SYS_CONF


class AclCore(object):

    def __init__(self):
        self.e = casbin.Enforcer(
            SYS_CONF["acl"]["auth_model"],
            SYS_CONF["acl"]["policy"],
            enable_log=False
        )

    def enforce(self, sub, obj, act):
        return self.e.enforce(sub, obj, act)

aclcore = AclCore()
