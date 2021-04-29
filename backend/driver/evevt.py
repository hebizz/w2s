import psutil

def get_psutil_info():
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    cpu = psutil.cpu_percent(0)
    if mem < 40 and disk < 40 and cpu < 40:
        status = "normal"
    else:
        status = "abnormal"
    return mem, disk, cpu, status

def get_event_info(k, v):
    if k == "cpu":
        res = round(psutil.cpu_percent(0), 1)
    elif k == "mem":
        res = round(psutil.virtual_memory().percent, 1)
    else:
        res = round(psutil.disk_usage("/").percent, 1)

    if res < 40:
        msg = "{}正常".format(v)
    elif 40 <= res <= 70:
        msg = "{}异常,已达到{}%".format(v, res)
    else:
        msg = "{}严重异常,已达到{}%".format(v, res)
    return msg, res
