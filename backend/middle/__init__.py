# 中间代理，用于解耦

class Middle:
    RT = None
    CldT = None

    @classmethod
    def initialize(cls, RT, CldT):
        cls.RT = RT
        cls.CldT = CldT
