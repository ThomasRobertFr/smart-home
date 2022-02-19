"""This module handles the logic of representing a calendar as a python object and provide ways
to interract with a calendar.
"""

import re
import unicodedata
from datetime import datetime
from typing import Tuple

import numpy as np

START_YEAR = 2020  # first year for which we record calendars
NB_DAYS_PER_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DAYS_PER_YEAR = sum(NB_DAYS_PER_MONTH)
EXPECTED_CALENDAR_LENGHT = DAYS_PER_YEAR * (datetime.now().year - START_YEAR + 1)


class Calendar:
    """Backend class that represent a calendar

    TODO Change the numpy storage to a Dict[int, List[RGB]]  # for year -> month -> day's rgb.
     This np array is not really useful and is a pain to use.
    """
    def __init__(self,
                 name: str,
                 color: Tuple[int, int, int],
                 id: str = None,
                 days: np.ndarray = None):
        self.id = id
        self.name = name
        self.color = color
        if days is not None:
            self.days = days
            self._ensure_valid_days()
        else:
            self.days = np.zeros((EXPECTED_CALENDAR_LENGHT, 3), dtype=np.uint8)

    def _ensure_valid_days(self):
        assert isinstance(self.days, np.ndarray)
        if len(self.days) < EXPECTED_CALENDAR_LENGHT:
            assert self.days.shape[1] == 3
            self.days = np.pad(
                self.days,
                [[0, EXPECTED_CALENDAR_LENGHT - self.days.shape[0]], [0, 0]],
                'constant',
            )

    def get_day(self, year, month, day):
        return self.days[self.get_day_index(year, month, day)].tolist()

    def set_day(self, year, month, day, on=True, color=None):
        index = self.get_day_index(year, month, day)
        if color is None:
            color = self.color if on else [0, 0, 0]
        color = np.asarray(color, dtype=np.uint8)
        assert color.shape == (3, )
        self.days[index] = color

    def to_dict(self, format_days=False, remove_days=False):
        out = {
            "id": self.id,
            "name": self.name,
            "color": list(self.color),
            "current_year": str(datetime.now().year),
        }
        if not remove_days:
            out["days"] = self.days if not format_days else self.format_days(binary=True)
        return out

    @classmethod
    def from_dict(cls, d):
        return cls(id=d.get("id"), name=d["name"], color=tuple(d["color"]), days=d["days"])

    def format_days(self, binary=True):
        out = {}
        for year in range(START_YEAR, datetime.now().year + 1):
            out[str(year)] = []
            for month, nb_days in zip(range(12), NB_DAYS_PER_MONTH):
                month_days = self.days[
                                self.get_day_index(year, month + 1, 1):
                                self.get_day_index(year, month + 1, nb_days) + 1
                             ]  # yapf: disable
                if binary:
                    month_days = month_days.max(axis=1).clip(0, 1)
                out[str(year)].append(month_days.tolist())
        return out

    @staticmethod
    def get_day_index(year, month, day):
        assert year >= START_YEAR
        assert 1 <= month <= 12
        assert 1 <= day <= NB_DAYS_PER_MONTH[month - 1]
        index = (year - START_YEAR) * DAYS_PER_YEAR  # e.g. 2020 -> 365
        index += sum(NB_DAYS_PER_MONTH[:month - 1])  # e.g. march -> 31 (jan) + 29 (feb)
        index += day - 1
        return index


class Calendars(dict):
    """A backend class to store all the calendars and their state. It inherits dict and can only
    contain `Calendar` objects as value.
    """
    def __setitem__(self, key: str, value: Calendar):
        assert isinstance(value, Calendar)
        value.id = key
        super(Calendars, self).__setitem__(key, value)

    def insert(self, calendar: Calendar):
        """Add a calendar in our collection"""
        self[self._name_to_id(calendar.name, create_new=True)] = calendar

    def dump(self):
        """Dump the calendars into a savable format"""
        return {k: v.to_dict() for k, v in self.items()}

    def load(self, payload):
        """Reload from a `dump()`"""
        for k in list(self.keys()):  # empty
            self.pop(k)
        for id, calendar in payload.items():
            self[id] = Calendar.from_dict(calendar)

    def _name_to_id(self, name, create_new=False):
        """Find a proper ID for a calendar's name"""
        id = self.slugify(name)
        if not create_new:
            return id
        add = ""
        while id + str(add) in self:
            if add == "":
                add = 1
            else:
                add += 1
        return id + str(add)

    @staticmethod
    def slugify(value: str):
        """Get a clean ASCII version of a string"""
        # if sys.version_info.major == 2:
        #     if not isinstance(value, unicode):
        #         value = unicode(value)
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        # if sys.version_info.major == 2:
        #     value = unicode(value)
        return re.sub(r'[-\s]+', '-', value)
