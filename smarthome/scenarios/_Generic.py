import abc
import copy
from typing import Type, Dict, List

from ..misc import config as _config
from ..misc.utils import load_from_string_import


class Scenario:
    @abc.abstractmethod
    def run(self):
        pass

    @staticmethod
    def load_from_dict(scenario: dict) -> 'Scenario':
        scenario_class: Type[Scenario] = load_from_string_import(scenario["class"])
        scenario = copy.deepcopy(scenario)
        for k in {"id", "idx", "class"}:
            if k in scenario:
                scenario.pop(k)
        try:
            return scenario_class(**scenario)
        except Exception as e:
            raise ValueError(f"Impossible to create object for scenario {scenario}") from e


class Scenarios:
    def __init__(self):
        self.list: List[dict] = [{"id": id, **scenar} for id, scenar in _config.get_dict()["scenarios"].items()]
        self.by_id_dict: Dict[str, dict] = {scenar["id"]: scenar for scenar in self.list}
        self.by_idx_dict: Dict[str, dict] = {scenar["idx"]: scenar for scenar in self.list}
        self.by_id: Dict[str, Scenario] = {scenar["id"]: Scenario.load_from_dict(scenar) for scenar in self.list}
        self.by_idx: Dict[str, Scenario] = {scenar["idx"]: Scenario.load_from_dict(scenar) for scenar in self.list}
