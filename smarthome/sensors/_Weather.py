import json
import os
import time
from enum import Enum

import pkg_resources
import requests

from ..misc import config as _config
config = _config.get().weather


class Weather:
    """Wrapper class for DarkSky API with a caching mechanism to avoid calling the API too much"""
    class Query(str, Enum):
        forecast = "forecast"
        hourly = "hourly"

    @staticmethod
    def _get_cache(query: Query):
        fname = pkg_resources.resource_filename("smarthome", f"data/weather_cache_{query}.json")
        if not os.path.exists(fname) or (time.time() - os.path.getmtime(fname)) > 60 * 60:
            return None
        try:
            out = json.load(open(fname, "r"))
            assert out
            return out
        except:
            return None

    @staticmethod
    def _set_cache(query: Query, content):
        fname = pkg_resources.resource_filename("smarthome", f"data/weather_cache_{query}.json")
        with open(fname, "w") as f:
            json.dump(content, f)

    @classmethod
    def get(cls, query: Query = Query.forecast):
        cache = cls._get_cache(query)
        if cache:
            return cache
        else:
            if query == cls.Query.forecast:
                r = requests.get(f"https://api.darksky.net/forecast/{config.key}/{config.location}?units=si")
                out = r.json()
            elif query == cls.Query.hourly:
                r = requests.get(f"https://api.darksky.net/forecast/{config.key}/{config.location}?units=si&extend=hourly")
                out = r.json()
            else:
                raise ValueError(f"Unknown weather query {query}")
            cls._set_cache(query, out)
            return out

