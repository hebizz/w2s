import ctypes
import logging


def call(dylib_list, func_name, *args):
    for dylib in dylib_list:
        try:
            lib = ctypes.CDLL(dylib)
            try:
                value = eval("lib.{}".format(func_name))(*args)
                logging.debug("call: {} @({})".format(dylib, func_name))
                logging.debug("return value: {}".format(str(value)))
                return value
            except:
                logging.error("eval failed(%s) @(%s)", dylib, func_name)
                continue
        except Exception as err:
            logging.error("load failed(%s): %s", dylib, err)
            continue
    raise RuntimeError("no entry: @({})".format(func_name))