from backend.driver.mongo import mongodb

def get(func_name):
    # intend to use one tuple to store this structure
    fetch = mongodb.pointer.find_one()
    if func_name == "":
        fetch.pop("_id")
        return fetch
    else:
        f = fetch.get(func_name)
        if f is None:
            raise RuntimeError("invalid function")
        return f

def update_all(data):
    mongodb.pointer.update_one({}, {"$set": data})
    return get("")