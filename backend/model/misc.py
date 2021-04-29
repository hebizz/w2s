# coding: utf-8


def check_field(data, required, prefix=None):
    if isinstance(required, list):
        for f in required:
            if isinstance(f, dict):
                for sf, sr in f.items():
                    if prefix:
                        pre = "{}.{}".format(prefix, sf)
                    else:
                        pre = sf
                    check_field(data[sf], sr, prefix=pre)
            elif f not in data:
                raise RuntimeError("{} not found".format(f))
    else:
        raise Exception("not supported check field function")
