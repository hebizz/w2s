import json
import requests
import logging

def get_register_data():
    url = "http://127.0.0.1:9000/internalapi/v1/register"
    payload = {
            "name": "guard",
            "host_port": "127.0.0.1:9002",
            "version": "v1",
            "health_check": "/api/v1/guard",
            "url_patterns": ["worker", "image", "map", "camera_setting"]
        }
    headers = {
        'Content-Type': "application/json",
        }
    return url, json.dumps(payload), headers


def register_api_gateway():

    url, payload, headers = get_register_data()
    response = requests.request("POST", url, data=payload, headers=headers)
    print("register_api_gateway: " +response.text)

def anti_register_api_gateway():

    url, payload, headers = get_register_data()
    response = requests.request("DELETE", url, data=payload, headers=headers)
    print("anti_register_api_gateway: " +response.text)

def _isInsidePolygon(pt, poly):
    """determine if a point is inside a polygon"""
    c = False
    i = -1
    l = len(poly)
    j = l -1
    while i < l - 1:
        i += 1

        if ((poly[i]["x"] <= pt["x"] and pt["x"] < poly[j]["x"]) or
            (poly[j]["x"] <= pt["x"] and pt["x"] < poly[i]["x"])):
            if (pt["y"] < (poly[j]["y"] - poly[i]["y"]) * (pt["x"] - poly[i]["x"]) /
               (poly[j]["x"] - poly[i]["x"]) + poly[i]["y"]):
                c = not c
        j = i
    return c

def reslove_result(filter_results, func_name):
    parse_results = {}
    for result in filter_results:
        if len(result) > 6:
            extra_info = result[6]
        else:
            extra_info = None
        result_info = {
            "probability": result[1],
            "xmin": result[2],
            "ymin": result[3],
            "xmax": result[4],
            "ymax": result[5],
            "extra": extra_info,
        }
        if func_name not in parse_results:
            parse_results[func_name] = [result_info]
        else:
            parse_results[func_name].append(result_info)
    return parse_results

def threshold_filter(ai_results, cam):
    threshold_result = {}
    cam_function = cam.function
    for func_name, func_results in ai_results.items():
        func_threshold_result = []
        func_threshold = cam_function[func_name].get("threshold", 0.2)
        logging.info("utils.threshold_filter:: threshold of func@{} is {}".format(func_name, func_threshold))
        for func_result in func_results:
            probability = func_result["probability"]
            if float(probability) >= float(func_threshold):
                func_threshold_result.append(func_result)
        if len(func_threshold_result) > 0:
            threshold_result[func_name] = func_threshold_result
    return threshold_result
