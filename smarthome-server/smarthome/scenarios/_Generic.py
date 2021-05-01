import abc
import copy
import time
from typing import Dict, List

from ..devices import Device, HueLamp
from ..misc import config as _config
from ..misc.wrappers import WrapperSet, Wrapper


class Scenario(Wrapper):
    @abc.abstractmethod
    def run(self):
        pass


class Scenarios(WrapperSet[Scenario]):
    def __init__(self, scenarios: Dict[str, dict] = None):
        if scenarios is None:
            scenarios = _config.get_dict()["scenarios"]
        super().__init__(Scenario, scenarios)


class BasicScenario(Scenario):
    def __init__(self, id: str, idx: int, devices: Dict[str, str]):
        from smarthome.server import DEVICES

        def process_val(v):
            if isinstance(v, bool):
                return "on" if v else "off"
            else:
                return str(v)

        super().__init__(id, idx)
        self.devices: Dict[Device, str] = {
            DEVICES[device]: process_val(val) for device, val in devices.items()
        }

    def run(self):
        for device, value in self.devices.items():
            device.put_domoticz(value, catch_error=True)

    def __repr__(self):
        dict = copy.copy(self.__dict__)
        dict["devices"] = {d.id: v for d, v in self.devices.items()}
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in dict.items()])})"


class BasicScenarioWithHue(BasicScenario):
    def __init__(self, id: str, idx: int, devices: Dict[str, str],
                 hue_calls: List[dict], hue_id: str = None, hue_idx: int = None):
        from smarthome.server import DEVICES

        super().__init__(id, idx, devices)
        self.hue_calls = hue_calls
        self.hue_device: HueLamp = DEVICES[hue_id or hue_idx]
        assert isinstance(self.hue_device, HueLamp)

    def run(self):
        super().run()
        for hue_call in self.hue_calls:
            self.hue_device.hue_api_call(hue_call)
            time.sleep(1)
