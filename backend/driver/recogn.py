import logging
import subprocess
import base64
import json
import random
import requests
import yaml

from backend.settings import SYS_CONF
from backend.driver import alert as altctl
from backend.driver import camera as camctl
from backend.driver import parse as parctl
from backend.driver import clock as clkctl
from backend.driver import exporter as expctl
from backend.driver import memory


FUNC_PARSE_MAP = {
    "fire": parctl.fire_filter("fire"),
    "restrict": parctl.restrict_filter("restrict"),
    "no_helmet": parctl.no_helmet_filter("no_helmet"),
    "pata": parctl.pata_filter("pata"),
    "smoke": parctl.smoke_filter("smoke"),
    "machinery": parctl.machinery_filter("machinery"),
    "move": parctl.move_filter("move"),
}

def period_function_filter(cam, mode="auto"):
    function_list = []
    if mode == "manual":
        function_list = list(cam.function)

    for function_type in cam.function:
        detection_enable = cam.function[function_type]["enable"]
        if not detection_enable:
            continue

        detection_cycle = cam.function[function_type]["detection_cycle"]
        if clkctl.check_period_filter(detection_cycle["detection_period"], detection_cycle["detection_time"]):
            function_list.append(function_type)

    return function_list

def ai_pointer_filter(function_list):
    total_func = []
    for func in function_list:
        dependencies = memory.FUNCTION_TABLE.get(func, {}).get('dependencies', [])
        total_func += dependencies
        total_func.append(func)
    total_func = list(set(total_func))

    model_list = []
    for func in total_func:
        pointer = memory.FUNCTION_TABLE.get(func, {}).get("pointer", [])
        model_list += pointer
    model_list = list(set(model_list))
    return model_list

def recognize(path, device_id, function_list, model_list):
    cam = camctl.get_one(device_id)
    if SYS_CONF["device"] == "TD201":
        raw_results = get_td201_ai()
    else:
        try:
            results = _request_cluster(path, model_list)
            raw_results = []
            for part, result in results.items():
                for item in result:
                    raw_results.append(item)
        except Exception as err:
            logging.exception(err)
            raise RuntimeError("invalid AI response: {}".format(err))

    parse_list = []
    for func in function_list:
        parse_list.append(FUNC_PARSE_MAP[func])
    warning_parser = parctl.Warning_Parser(parse_list)
    parse_results = warning_parser(raw_results, cam)

    if parse_results:
        export_info = SYS_CONF["exporter"]
        if export_info.get("enable", False):
            expctl.export(parse_results, path, cam)

        url = path.split("w2s/")[1]
        for k, v in parse_results.items():
            altctl.create(cam=cam, func_name=k, result_info=v, image_path=url)
    return parse_results

def _request_cluster(path, model_list):
    results = {}

    image_extra_command = SYS_CONF.get("image_extra_command", {})

    with open(path, 'rb') as f:
        img = str(base64.b64encode(f.read()), encoding='utf-8')

    for model, model_info in SYS_CONF['chip_pointer'].items():
        if model not in model_list:
            continue
        address_list = model_info.get('address', [])
        if not address_list:
            raise RuntimeError("image {} owns none chip!".format(model))
        extra_command = image_extra_command[model]
        schedule_index = random.randint(0, len(address_list)-1)
        node_address = address_list[schedule_index]

        logging.info("image %s @ recogn requesting: %s" %(model, node_address))
        requests_command = {'image': img}
        requests_command.update(extra_command)
        response = requests.post("http://{}/api/detect".format(node_address),
                                 data=json.dumps(requests_command),
                                 timeout=3)
        response = response.json()['result']
        if type(response).__name__ == 'dict':
            temp = list(response.values())
            part_results = []
            for i in temp:
                t = json.loads(i)
                part_results += t
        else:
            part_results = json.loads(response)
        results[model] = part_results
    return results

    # 东视摄像头上调用使用，需要区分设备来调用
    # for model, model_info in memory.CHIP_POINTER_TABLE.items():
    #     if model not in model_list:
    #         continue
    #     # resp1 DL
    #     resp1 = eval(subprocess.check_output(['/app/backend/model/yolo', '/app/backend/model/data_process', path]))
    #     # resp2 CV
    #     resp2 = memory.MOVE_MODEL.compute(path)
    #     results[model] = resp1 + resp2
    # return results

def get_td201_ai():
    with open(SYS_CONF["TD201_airesult_path"]) as f:
        tmp = json.load(f)
    ai_id = tmp.get("msg_id")
    # td201 如果有ai结果, msg_id则会更新
    logging.info(ai_id)
    logging.info(memory.TD201_AI_ID)
    if ai_id == memory.TD201_AI_ID:
        results = []
        logging.info("TD201 ai results: {}".format(results))
        return results
    else:
        memory.TD201_AI_ID = ai_id
        results = tmp.get("results", [])
        logging.info("TD201 ai results: {}".format(results))
        return results

