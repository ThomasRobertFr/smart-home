from flask_restful import Resource
import requests
import json


class Calendar(Resource):
    def put(self, verb, param):
        try:
            r = requests.put(f"http://raspi/calendar/display/{verb}/{param}", timeout=1)
            return json.loads(r.content.decode("utf-8"))
        except:
            return
