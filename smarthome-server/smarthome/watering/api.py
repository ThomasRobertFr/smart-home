import re
from typing import Dict

import yaml
from fastapi import APIRouter

from .lib import WateringDevice, WateringReport

router = APIRouter(prefix="/watering", tags=["watering"])


@router.get("")
@router.get("/")
def get_devices(full: bool = False) -> Dict[str, Dict]:
    """List devices"""
    return {d.id: d.as_dict(full=full) for d in WateringDevice.list_devices()}


@router.post("")
@router.post("/")
def add_device(device: WateringDevice, full: bool = False) -> Dict:
    """Create a new device"""
    return device.insert_in_db().as_dict(full=full)


@router.post("/{id}")
def add_device_id(id: str, full: bool = False) -> Dict:
    """Create a new device with provided id"""
    return WateringDevice(id=id).insert_in_db().as_dict(full=full)


@router.get("/{id}")
def get_device(id: str, full: bool = False) -> Dict:
    """Get a device by id, show all info if `full` set to True"""
    return WateringDevice.load_from_db(id).as_dict(full=full)


@router.delete("/{id}")
def delete_device(id: str, full: bool = False) -> Dict:
    """Remove a device"""
    return WateringDevice.load_from_db(id).remove_from_db().as_dict(full=full)


@router.patch("/{id}")
def edit_device(id: str, key: str, value: str):
    """Edit field `key` with provided `value` for device `id`. The value will be formatted by
    `yaml.full_load(...)`.
    """
    if re.match(r"^[0-9.+*\-/ \t]+$", value):
        value = int(eval(value))
    else:
        value = yaml.full_load(value)

    WateringDevice.load_from_db(id).update({key: value}).update_in_db()
    return value


@router.post("/{id}/report")
def report_device(id: str, report: WateringReport):
    """Send a watering report for a given device"""
    WateringDevice.load_from_db(id).update_with_report(report).update_in_db()
