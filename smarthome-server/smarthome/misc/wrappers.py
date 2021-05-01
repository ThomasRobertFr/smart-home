import copy
from typing import Type, List, Dict, Union, Generic, TypeVar

from smarthome.misc.utils import load_from_string_import
from smarthome.misc import config as _config

config = _config.get()


class Wrapper:
    def __init__(self, id: str, idx: int):
        self.id = id
        self.idx = idx

    @classmethod
    def load_from_dict(cls, definition: dict):
        class_to_use: Type[cls] = load_from_string_import(definition["class"])
        definition = copy.deepcopy(definition)
        if "idx" not in definition:
            definition["idx"] = -1
        definition.pop("class")
        try:
            return class_to_use(**definition)
        except Exception as e:
            raise ValueError(f"Impossible to create from definition {definition}") from e

    def __repr__(self):
        return f"{self.__class__.__name__}" \
               f"({', '.join([f'{k}={v}' for k, v in self.__dict__.items()])})"


T = TypeVar('T', bound=Wrapper)


class WrapperSet(Generic[T]):
    def __init__(self, wrapper_class: Type[T], definitions: Dict[str, dict]):
        # This is not perfect but could not find how to access the value provided to T to be able
        # to call static method `load_from_dict` on it, so asking to give it as input.
        self.wrapper_class = wrapper_class

        self.list_dict: List[dict] = [{"id": id, **wrap} for id, wrap in definitions.items()]
        self.by_id_dict: Dict[str, dict] = {wrap["id"]: wrap for wrap in self.list_dict}
        self.by_idx_dict: Dict[int, dict] = {wrap.get("idx"): wrap for wrap in self.list_dict}

        self.list: List[T] = [wrapper_class.load_from_dict(device) for device in self.list_dict]
        self.by_id: Dict[str, T] = {device.id: device for device in self.list}
        self.by_idx: Dict[int, T] = {device.idx: device for device in self.list}

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.by_id
        if isinstance(item, int):
            return item in self.by_idx

    def __getitem__(self, item: Union[str, int]) -> T:
        if isinstance(item, str):
            return self.by_id[item]
        if isinstance(item, int):
            return self.by_idx[item]

    def __str__(self):
        return self.wrapper_class.__name__ + "s:\n" + "\n".join(f'- {d}' for d in self.list)
