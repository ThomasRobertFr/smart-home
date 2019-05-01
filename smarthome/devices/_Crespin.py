from flask_restful import Resource, reqparse
import socket
import os
import time
from datetime import datetime, timedelta
from ..misc import config as _config
from ..devices import PowerPlug
config = _config.get().crespin

parser = reqparse.RequestParser()
parser.add_argument('data')

class Crespin(Resource):

    status = "unkn"
    status_time = datetime.now() - timedelta(days=100)

    def _set_status(self, status):
        Crespin.status = status
        Crespin.status_time = datetime.now()

    def get(self):
        if (datetime.now() - Crespin.status_time).total_seconds() > 120:
            if os.system("ping -c 1 -t 2 " + config.ip) == 0:
                self._set_status("on")
            else:
                self._set_status("off")
        return Crespin.status

    def put(self, status):
        if status == "on" and self.get() != "on":
            self._set_status("on")
            PowerPlug().put("crespin-mobile", "on")
        elif status == "off" and self.get() != "off":
            self._set_status("off")
            self.send("shutdown")
            time.sleep(10)
            PowerPlug().put("crespin-mobile", "off")

    def post(self):
        args = parser.parse_args()
        return self.send(args["data"])

    def send(self, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((config.ip, config.port))
                s.sendall(data.encode("ascii"))
                return s.recv(1024).decode()
        except:
            return "ERR Failed to send command"
