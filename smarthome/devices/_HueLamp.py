from flask_restful import Resource
import requests
from ..misc import config as _config
config = _config.get().hue


class HueLamp(Resource):

    def get(self, id):
        url = "http://%s/api/%s/lights/%s" % (config.host, config.username, id)
        r = requests.get(url)
        return r.json()
        # TODO handle errors

    def put(self, id, data):
        url = "http://%s/api/%s/lights/%s/state" % (config.host, config.username, id)
        r = requests.put(url, json=data)
        print(r.json())
        return r.json()
        # TODO handle errors

