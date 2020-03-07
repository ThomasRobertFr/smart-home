from flask_restful import Resource
import requests
import json

class Calendar(Resource):
    def put(self, verb, param):
        r = requests.put("http://raspi/calendar/display/"+verb+"/"+param, timeout=1)
        return json.loads(r.content.decode("utf-8"))

