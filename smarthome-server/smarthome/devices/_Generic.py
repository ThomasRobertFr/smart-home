import abc
import logging
from typing import Dict

import requests

from smarthome.misc import config as _config
from smarthome.misc.wrappers import Wrapper, WrapperSet

config = _config.get()


class Device(Wrapper):
    @abc.abstractmethod
    def put(self, value: str):
        """Change the status of this device based on provided value (accepted values will depend on
        the implementation of the device).
        """

    @abc.abstractmethod
    def get_domoticz_url(self, value: str) -> str:
        """Return the end of the URL to change the status of this device via Domoticz."""

    def put_domoticz(self, value: str, catch_error: bool = False) -> bool:
        """Change the status of this device via Domoticz. This will end up calling this code back
        via `put` but will register the changed state in Domoticz. We could probably do this in
        many other ways like sending a message to Domoticz's MQTT but for now this will do the
        trick.
        """
        if not isinstance(value, str):
            value = str(value)
        url = "[not defined]"
        try:
            assert config.domoticz.base_url_json.endswith("json.htm?")
            url = f"{config.domoticz.base_url_json}idx={self.idx}&{self.get_domoticz_url(value)}"
            req = requests.get(url)
            req.raise_for_status()
            if req.json().get("status") != "OK":
                raise RuntimeError(f"Domoticz did not return status=OK, got {req.json()}")
            return True
        except Exception as e:
            if catch_error:
                logging.error(f"Failed during domoticz call to {url}: {e}")
                return False
            else:
                raise RuntimeError(f"Failed during domoticz call to {url}: {e}") from e


class Devices(WrapperSet[Device]):
    def __init__(self, devices: Dict[str, dict] = None):
        if devices is None:
            devices = _config.get_dict()["devices"]
        super().__init__(Device, devices)


class PushButton(Device):
    @abc.abstractmethod
    def push(self):
        pass

    def put(self, value: str):
        value = value.lower().strip()
        if value in {"on", "off", "push"}:
            self.push()
        else:
            raise ValueError(f"Invalid value '{value}' (on, off, push)")

    def get_domoticz_url(self, value: str) -> str:
        value = value.lower().strip()
        if value in {"on", "off", "push"}:
            return "type=command&param=switchlight&switchcmd=On"
        else:
            raise ValueError(f"Invalid value '{value}' (on, off, push)")


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
            raise ValueError(f"Invalid value '{value}' (on, off)")

    def get_domoticz_url(self, value: str) -> str:
        value = value.lower().strip()
        if value == "on":
            return "type=command&param=switchlight&switchcmd=On"
        elif value == "off":
            return "type=command&param=switchlight&switchcmd=Off"
        else:
            raise ValueError(f"Invalid value '{value}' (on, off)")


class Dimmer(Switch):
    @abc.abstractmethod
    def set_level(self, value: float):
        """value should be in [0, 100] interval with 0 == off and 100 == on"""
        pass

    def put(self, value: str):
        # Try with parent first
        try:
            return super().put(value)
        except ValueError:
            pass

        # Else try with our set_level
        try:
            self.set_level(float(value))
        except ValueError:
            raise ValueError(f"Invalid value '{value}' (on, off or float for level)")

    def get_domoticz_url(self, value: str) -> str:
        # Try with parent first
        try:
            return super().get_domoticz_url(value)
        except ValueError:
            pass

        # Else try with our set_level
        try:
            value = float(value)
            return f"type=command&param=switchlight&switchcmd=Set%20Level&level={value}"
        except ValueError:
            raise ValueError(f"Invalid value '{value}' (on, off or float for level)")
