from flask_restful import Resource
from ._Arrive import Arrive
from ._Bedtime import Bedtime
from datetime import datetime

class ArriveOrBedtime(Resource):

    def put(self):
        if datetime.now().hour > 7 and datetime.now().hour < 22:
            Arrive().put()
        else:
            Bedtime().put()
