"""
TODO adapt to fastapi

import copy
import distutils.util
import os
import re
import time

from flask import request
from flask_restful import Resource
from flask_restful import abort
from flask_restful import reqparse
# from ..misc import config as _config
import pickle as pkl
# config = _config.get().watering

edit_parser = reqparse.RequestParser()
edit_parser.add_argument('key', type=str)
edit_parser.add_argument('value', type=str)


class WateringSensors(Resource):
    default_sensor = {
        "id": "default",

        "sensor_exist": True,
        "calibrations": [],
        "calibrate": True,  # run a calibration at boot
        "calibration_duration": 30,  # 30s
        "calibration_min": 1023,
        "calibration_max": 0,

        "measures": [],
        "measure_interval": 60 * 60,  # 1h

        "waterings": [],
        "watering": False,  # watering disabled
        "watering_scheduled": False,  # watering based on scheduling
        "watering_scheduling_start_bound": 0,  # bounds in which scheduled watering can occur
        "watering_scheduling_end_bound": 24*60*60,  # bounds in which scheduled watering can occur
        "watering_last": 0,  # timestamp of last watering
        "watering_humidity_threshold": 30,  # 30%, water if < threshold
        "watering_humidity_target": 60,  # 60%, watering stop if > target
        "watering_cycle_nb_max": 30,  # max 30 cycles of Xs of pumping
        "watering_cycle_duration": 5,  # 5s
        "watering_cycle_sleep": 5,  # 5s
        "watering_cooldown": 60 * 60 * 3,  # sleep for 3h after watering
    }
    hide_not_full = ["sensor_exist", "watering_scheduled",
                     "watering_scheduling_start_bound", "watering_scheduling_end_bound"]
    data = {}

    def get(self, id=None):
        if not WateringSensors.data and os.path.exists("data/watering.pkl"):
            with open("data/watering.pkl", "rb") as f:
                WateringSensors.data = pkl.load(f)
                # add possibly missing keys
                for sensor in WateringSensors.data.values():
                    for k, v in self.default_sensor.items():
                        if k not in sensor:
                            sensor[k] = v

        for d in WateringSensors.data.values():
            d["watering_last_delta"] = int(time.time()) - int(d["watering_last"])

        if id is None:
            return WateringSensors.data
        else:
            if id not in WateringSensors.data:
                abort(404, message="Sensor {} does not exist.".format(id))
            return WateringSensors.data[id]

    def exists(self, id):
        self.get()
        return id in WateringSensors.data

    def add_sensor(self, id):
        if id in self.get():
            abort(403, message="Sensor {} already exist.".format(id))

        data = copy.deepcopy(WateringSensors.default_sensor)
        data["id"] = id
        self.get()[id] = data
        self.save()

    def remove_sensor(self, id):
        self.get()  # load data and check exists
        del WateringSensors.data[id]
        self.save()

    def set_sensor(self, id, data):
        self.get(id)  # load, check exists
        WateringSensors.data[id] = data
        self.save()

    def save(self):
        with open("data/watering.pkl", "wb") as f:
            pkl.dump(WateringSensors.data, f)


class WateringSensor(Resource):
    def get(self, id, verb=""):
        data = WateringSensors().get(id).copy()
        data["watering_last_delta"] = int(time.time()) - data["watering_last"]
        data["force_watering"] = False
        if data["watering_scheduled"] and data["watering"]:
            if (data["watering_last_delta"] - data["watering_cooldown"]) / data["watering_cooldown"] > -0.05:
                data["force_watering"] = True
        if verb != "full":
            for k in list(data.keys()):
                if isinstance(data[k], list):
                    del data[k]
            if not data["sensor_exist"] and data["calibrate"]:
                data["calibrate"] = False
            for k in WateringSensors.hide_not_full:
                del data[k]
        return data

    def put(self, id, verb=""):
        if verb not in ["report", "edit"]:
            abort(403, message="Incorrect verb")

        data = WateringSensors().get(id)

        if verb == "edit":
            args = edit_parser.parse_args()
            key, val = args["key"], args["value"]
            if key not in data:
                abort(403, message="Incorrect key " + key)
            if isinstance(data[key], bool):
                try:
                    data[key] = bool(distutils.util.strtobool(val))
                except ValueError:
                    abort(403, message="Incorrect value for boolean " + val)
            elif isinstance(data[key], int):
                try:
                    if re.match(r"^[0-9.+*\-/ \t]+$", val):
                        data[key] = int(eval(val))
                    else:
                        raise ValueError()
                except:
                    abort(403, message="Incorrect value for number " + val)
            elif isinstance(data[key], str):
                data[key] = val
            else:
                abort(403, message="Unsupported edit type for " + key)

            WateringSensors().set_sensor(id, data)
            return data[key]

        elif verb == "report":
            reqdata = request.get_json()
            first_time = None
            if "measures" in reqdata and isinstance(reqdata["measures"], list):
                reqdata["measures"].reverse()
                measures = []
                for m in reqdata["measures"]:
                    if isinstance(m, list) and len(m) == 2:
                        if first_time is None:
                            first_time = m[0]
                        measures.append([int(time.time()) + m[0] - first_time, m[1]])
                measures.reverse()
                data["measures"] += measures

            if "calibrations" in reqdata and isinstance(reqdata["calibrations"], list):
                for v in reqdata["calibrations"]:
                    if isinstance(v, int) or isinstance(v, float):
                        data["calibrations"].append([int(time.time()) - 60, v])
                        if v < data["calibration_min"]:
                            data["calibration_min"] = v
                        if v > data["calibration_max"]:
                            data["calibration_max"] = v

            if "waterings" in reqdata and isinstance(reqdata["waterings"], int) and reqdata["waterings"] > 0:
                watering_timestamp = int(time.time()) - first_time if first_time is not None else int(time.time()) - 30
                data["waterings"].append([watering_timestamp, reqdata["waterings"]])
                data["watering_last"] = watering_timestamp

            WateringSensors().set_sensor(id, data)

            return "OK"

    def post(self, id):
        WateringSensors().add_sensor(id)
        return self.get(id, "full")

    def delete(self, id):
        WateringSensors().remove_sensor(id)
        return "OK"
"""
