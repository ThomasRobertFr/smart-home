import abc
import copy
from typing import Type, List, Dict

from ..misc.utils import load_from_string_import
from ..misc import config as _config


class Device:
    @abc.abstractmethod
    def put(self, value: str):
        pass

    @staticmethod
    def load_from_dict(device: dict) -> 'Device':
        device_class: Type[Device] = load_from_string_import(device["class"])
        device = copy.deepcopy(device)
        for k in {"id", "idx", "class"}:
            if k in device:
                device.pop(k)
        try:
            return device_class(**device)
        except Exception as e:
            raise ValueError(f"Impossible to create object for device {device}") from e


class Devices:
    def __init__(self):
        self.list: List[dict] = [{"id": id, **device} for id, device in _config.get_dict()["devices"].items()]
        self.by_id_dict: Dict[str, dict] = {device["id"]: device for device in self.list}
        self.by_idx_dict: Dict[str, dict] = {device["idx"]: device for device in self.list}
        self.by_id: Dict[str, Device] = {device["id"]: Device.load_from_dict(device) for device in self.list}
        self.by_idx: Dict[str, Device] = {device["idx"]: Device.load_from_dict(device) for device in self.list}


class PushButton(Device):
    @abc.abstractmethod
    def push(self):
        pass

    def put(self, value: str):
        value = value.lower().strip()
        if value == "on":
            self.push()
        elif value == "off":
            self.push()
        elif value == "push":
            self.push()
        else:
            raise ValueError("Invalid value")


class Switch(Device):
    @abc.abstractmethod
    def on(self):
        pass

    @abc.abstractmethod
    def off(self):
        pass

    def put(self, value: str):
        value = value.lower().strip()
        if value == "on":
            self.on()
        elif value == "off":
            self.off()
        else:
            raise ValueError("Invalid value")


class Dimmer(Switch):
    @abc.abstractmethod
    def set_level(self, value: float):
        """value should be in [0, 100] interval with 0 == off and 100 == on"""
        pass

    def put(self, value: str):
        # Try with parent first
        try:
            super().put(value)
        except ValueError:
            pass

        # Else try with our set_level
        try:
            self.set_level(float(value))
        except ValueError as e:
            raise ValueError("Invalid value") from e
