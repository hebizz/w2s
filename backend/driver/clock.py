import time
import datetime


def now():
    ts = _unix10ts()
    return _get_csttz_dt(ts), _get_utctz_dt(ts), ts

def second_elapse_today():
    local_time, _, _ = now()
    timestamp = local_time.hour*3600 + local_time.minute*60 + local_time.second
    weekday = local_time.weekday()
    return timestamp, weekday

def d13to10(ts):
    return int(round(ts/1000))

def u10to13(ts):
    return int(round(ts*1000))

def _get_utctz_dt(ts):
    """UTC Timezone, ts required 10digits"""
    return datetime.datetime.utcfromtimestamp(ts)

def _get_csttz_dt(ts):
    """CST(China Standard Time/UTC+8) Timezone, ts required 10digits"""
    return _get_utctz_dt(ts) + datetime.timedelta(hours=8)

def format_dt(dt):
    return dt.strftime("%Y-%m-%d-%H-%M-%S")

def format_dt_readable(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_dt_standard(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + time.strftime('%z')

def _unix13ts():
    """Return 13 digits Unix Timestamp (UTC), unit: ms"""
    return int(round(time.time()*1000))

def _unix10ts():
    """Return 10 digits Unix Timestamp (UTC), unit: sec"""
    return int(round(time.time()))


def check_period_filter(detection_period, detection_time):
    '''
    return false if not in detection period and time
    '''
    if detection_period is None or len(detection_period) == 0:
        return False

    if detection_time is None or len(detection_time) == 0:
        return False

    timestamp, weekday = second_elapse_today()
    if weekday not in detection_period:
        return False

    for dt_time in detection_time:
        if dt_time["starttime"] <= timestamp <= dt_time["endtime"]:
            return True
    return False
