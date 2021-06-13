import abc
import copy
import time
from typing import Dict, List

from smarthome.devices import Device, Dimmer, HueLamp
from smarthome.misc import config as _config
from smarthome.misc.utils import TypedDict
from smarthome.misc.wrappers import Wrapper, WrapperSet
from smarthome.sequences import (SequenceToRun, call_domoticz, run_sequence_group, wait)


class DimmingSetup(TypedDict):
    start: int  # 1 to 100
    end: int  # 1 to 100
    duration: int  # seconds


class Scenario(Wrapper):
    @abc.abstractmethod
    def run(self):
        pass


class Scenarios(WrapperSet[Scenario]):
    def __init__(self, scenarios: Dict[str, dict] = None):
        if scenarios is None:
            scenarios = _config.get_dict()["scenarios"]
        super().__init__(Scenario, scenarios)


class ParametricScenario(Scenario):
    def __init__(self,
                 id: str,
                 idx: int,
                 devices: Dict[str, str],
                 dimmings: Dict[str, DimmingSetup] = None,
                 hue_calls: List[dict] = None,
                 hue_id: str = None,
                 hue_idx: int = None):
        from smarthome.api import DEVICES

        def process_val(v):
            if isinstance(v, bool):
                return "on" if v else "off"
            else:
                return str(v)

        super().__init__(id, idx)
        self.devices: Dict[Device, str] = {
            DEVICES[device]: process_val(val)
            for device, val in devices.items()
        }

        # Hue device if provided. TODO change this to be supported by the generic devices field
        self.hue_calls = hue_calls or []
        self.hue_device = None
        if self.hue_calls:
            self.hue_device: HueLamp = DEVICES[hue_id or hue_idx]
            assert isinstance(self.hue_device, HueLamp)

        # Dimming
        self.dimmings: Dict[Device, DimmingSetup] = {
            DEVICES[device]: dimming
            for device, dimming in (dimmings or {}).items()
        }
        for device in self.dimmings.keys():
            assert isinstance(device, Dimmer)

    def run(self):
        for device, value in self.devices.items():
            device.put_domoticz(value, catch_error=True)

        for hue_call in self.hue_calls:
            self.hue_device.hue_api_call(hue_call)
            time.sleep(1)

        sequences = []
        for device, dimming in self.dimmings.items():
            step = -1 if dimming["end"] < dimming["start"] else 1
            steps = list(range(dimming["start"], dimming["end"] + step, step))
            duration_by_step = dimming["duration"] / len(steps)

            sequence: SequenceToRun = {
                "id": device.id,
                "device_id": device.id,
                "device_idx": device.idx,
                "tasks": []
            }
            for i, step in enumerate(steps):
                url = device.get_full_domoticz_url(str(step))
                sequence["tasks"].append(call_domoticz.si(url))
                if i < len(steps) - 1:
                    sequence["tasks"].append(wait.si(duration_by_step))
            sequences.append(sequence)
        run_sequence_group(self.id, sequences, use_name_as_id=True)

    def __repr__(self):
        dict = copy.copy(self.__dict__)
        dict["devices"] = {d.id: v for d, v in self.devices.items()}
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in dict.items()])})"
