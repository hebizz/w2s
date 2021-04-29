def merge(source, destination):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination

def get_config_camera():
    return dict(
        image = {
            "interval_second" : 30,
            "upload": {
                "enabled": True,     
                "only_alert": True,
            }
        },
        video = {
            "segment_second": 600,
            "upload": {
                "enabled": True,     
                "only_alert": True,
            }
        }
    )

def get_config_alert():
    return dict(
        alert_rule = {
                "enabled": True,
                "rules": {
                        "read_work_tickets": {
                                "enabled": False,
                                "cooldown": 1800,
                        },
                        "ground_rods": {
                                "enabled": False,
                                "cooldown": 1800,
                        },
                        "helmets": {
                                "enabled": False,
                                "cooldown": 300,
                                "limit": 1,
                        },
                        "insulated_gloves": {
                                "enabled": False,
                                "cooldown": 300,
                                "limit": 1
                        },
                        "fire": {
                                "enabled": False,
                                "cooldown": 300,
                                "limit": 1
                        }
            }
        }
    )



