from flask_restful import Resource
import requests
import datetime
from ..misc import config as _config
config = _config.get().weather


class Weather(Resource):

    cache_f = None
    cache_f_date = None
    cache_h = None
    cache_h_date = None

    def get(self, type="forecast"):

        if type == "forecast":
            if not self.cache_f or not datetime.datetime.now() - self.cache_f_date < datetime.timedelta(hours=1):
                r = requests.get("https://api.darksky.net/forecast/%s/%s?units=si" % (config.key, config.location))
                self.cache_f = r.json()
                self.cache_f_date = datetime.datetime.now()

            return self.cache_f

        if type == "hourly":
            if not self.cache_h or not datetime.datetime.now() - self.cache_h_date < datetime.timedelta(hours=1):
                r = requests.get("https://api.darksky.net/forecast/%s/%s?units=si&extend=hourly" % (config.key, config.location))
                self.cache_h = r.json()
                self.cache_h_date = datetime.datetime.now()

            return self.cache_h

