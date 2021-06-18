import time
from datetime import datetime, timedelta
from typing import Any, List, Tuple

import pkg_resources
from pydantic import BaseModel
from tinydb import Query, TinyDB

DB = TinyDB(pkg_resources.resource_filename("smarthome", "data/watering.json"))
DB_TABLE = DB.table("watering")


class WateringReport(BaseModel):
    measures: List[Tuple[int, int]] = None  # [timedelta, raw humidity measure]
    calibrations: List[int] = None  # raw humidity measures
    waterings: int = None  # nb of watering cycles


class WateringDevice(BaseModel):
    id: str

    sensor_exist: bool = True
    calibrations: List[Tuple[int, int]] = []  # [timestamp, raw humidity measure]
    calibrate: bool = True  # run a calibration at boot
    calibration_duration: int = 30  # 30s
    calibration_min: int = 1023
    calibration_max: int = 0

    measures: List[Tuple[int, int]] = []  # [timestamp, raw humidity measure]
    measure_interval: int = 60 * 60  # 1h

    waterings: List[Tuple[int, int]] = []  # [timestamp, watering duration]
    watering: bool = False  # watering disabled
    watering_scheduled: bool = False  # watering based on scheduling
    watering_scheduling_start_bound: int = 0  # bounds in which scheduled watering can occur
    watering_scheduling_end_bound: int = 24 * 60 * 60  # bound in which scheduled watering can occur
    watering_last: int = 0  # timestamp of last watering
    watering_humidity_threshold: int = 30  # 30%, water if < threshold
    watering_humidity_target: int = 60  # 60%, watering stop if > target
    watering_cycle_nb_max: int = 30  # max 30 cycles of Xs of pumping
    watering_cycle_duration: int = 5  # 5s
    watering_cycle_sleep: int = 5  # 5s
    watering_cooldown: int = 60 * 60 * 3  # sleep for 3h after watering

    class Config:
        extra = 'forbid'
        validate_assignment = True

    @property
    def force_watering(self) -> bool:
        return self.watering_scheduled and self.watering and \
               (self.watering_last_delta - self.watering_cooldown) / self.watering_cooldown > -0.05

    @property
    def watering_last_delta(self) -> int:
        return int(time.time()) - int(self.watering_last)

    def is_in_db(self) -> bool:
        query = Query()
        return bool(DB_TABLE.get(query.id == self.id))

    def insert_in_db(self) -> 'WateringDevice':
        if self.is_in_db():
            raise ValueError(f"Device {self.id} in DB, cannot insert it")
        DB_TABLE.insert(self.dict())
        return self

    def update_in_db(self) -> 'WateringDevice':
        if not self.is_in_db():
            raise ValueError(f"Device {self.id} not in DB, cannot update it")
        query = Query()
        DB_TABLE.upsert(self.dict(), query.id == self.id)
        return self

    def remove_from_db(self) -> 'WateringDevice':
        if not self.is_in_db():
            raise ValueError(f"Device {self.id} not in DB, cannot remove it")
        query = Query()
        DB_TABLE.remove(query.id == self.id)
        return self

    def update(self, update_fields: dict) -> 'WateringDevice':
        return WateringDevice(**{**self.dict(), **update_fields})

    def as_dict(self, full=True):
        out = self.dict()
        out["watering_last_delta"] = self.watering_last_delta
        out["force_watering"] = self.force_watering

        if not full:
            for k in {
                    "calibrations", "measures", "waterings", "sensor_exist", "watering_scheduled",
                    "watering_scheduling_start_bound", "watering_scheduling_end_bound"
            }:
                out.pop(k, None)

        return out

    @classmethod
    def load_from_db(cls, id: str) -> 'WateringDevice':
        query = Query()
        doc = DB_TABLE.get(query.id == id)
        if not doc:
            raise ValueError(f"Device {id} not in DB")
        return cls(**doc)

    @classmethod
    def list_devices(cls) -> 'List[WateringDevice]':
        return [cls(**d) for d in DB_TABLE.all()]

    def cleanup_data(self):
        """Remove old data to not have a too heavy database and also be able to plot stuff without
        having too much data.
        """
        one_month_ago = (datetime.now() - timedelta(weeks=5)).timestamp()
        one_weeks_ago = (datetime.now() - timedelta(weeks=1)).timestamp()

        def filter_list(l: List[Tuple[int, Any]], subsample_frequency):
            l_filtered = []
            t_last = 0
            for t, v in sorted(l, key=lambda _: _[0]):
                # More than a month ago: skip
                if t < one_month_ago:
                    continue
                # Between 1 month and 1 week ago, subsample to subsample_frequency
                elif t < one_weeks_ago and len(l_filtered) and t - t_last < subsample_frequency:
                    continue
                else:
                    l_filtered.append((t, v))
                    t_last = t
            return l_filtered

        self.measures = filter_list(self.measures,
                                    subsample_frequency=timedelta(hours=12).total_seconds())
        self.calibrations = filter_list(self.calibrations, subsample_frequency=0)
        self.waterings = filter_list(self.waterings, subsample_frequency=0)

    def update_with_report(self, report: WateringReport) -> 'WateringDevice':
        """Apply a report to the device, modifies it in place, returns `self`."""

        self.cleanup_data()  # Start with a cleanup before adding more data

        latest_measure_delta = 0
        if report.measures:
            latest_measure_delta = report.measures[-1][0]
            self.measures += [(int(time.time()) + m[0] - latest_measure_delta, m[1])
                              for m in report.measures]

        if report.calibrations:
            self.calibrations += [[int(time.time()) - 60, v] for v in report.calibrations]
            if self.calibration_min > min(report.calibrations):
                self.calibration_min = min(report.calibrations)
            if self.calibration_max < max(report.calibrations):
                self.calibration_max = max(report.calibrations)

        if report.waterings:
            self.watering_last = int(time.time()) - latest_measure_delta
            self.waterings.append((self.watering_last, report.waterings))

        return self
