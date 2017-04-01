from flask import Flask, Response
from flask_restful import Api
#import threading

# flask init
app = Flask(__name__)
api = Api(app)

# scenarios
from .scenarios import WakeUp, Leave, Sleep, Arrive, Bedtime, Party, ArriveOrBedtime
api.add_resource(WakeUp, '/scenarios/wakeup')
api.add_resource(Leave, '/scenarios/leave')
api.add_resource(Sleep, '/scenarios/sleep')
api.add_resource(Party, '/scenarios/party')
api.add_resource(Bedtime, '/scenarios/bedtime')
api.add_resource(Arrive, '/scenarios/arrive')
api.add_resource(ArriveOrBedtime, '/scenarios/arrive-or-bedtime')

# devices
from .devices import HueLamp, Radio, PowerPlug, PowerPlugs, RemotePilotWire, NAS, MistLamp
api.add_resource(HueLamp, '/devices/hue-lamp/<id>')
api.add_resource(Radio, '/devices/radio/<action>')
api.add_resource(RemotePilotWire, '/devices/remote-pilot-wire', '/devices/remote-pilot-wire/<action>')
api.add_resource(MistLamp, '/devices/mist-lamp', '/devices/mist-lamp/<command>')
api.add_resource(PowerPlugs, '/devices/power-plugs')
api.add_resource(PowerPlug, '/devices/power-plug/<id>', '/devices/power-plug/<id>/<status>')
api.add_resource(NAS, '/devices/nas', '/devices/nas/<status>')

# triggers
from .triggers import CalendarUpdate, CalendarTrigger
api.add_resource(CalendarUpdate, '/triggers/calendar/update')
api.add_resource(CalendarTrigger, '/triggers/calendar/trigger')

# sensors
from .sensors import Sun, Weather, State, Threads, Temperature
api.add_resource(Sun, '/sensors/sun')
api.add_resource(State, '/sensors/state')
api.add_resource(Temperature, '/sensors/temperature')
api.add_resource(Threads, '/sensors/threads', '/sensors/threads/<id>')
api.add_resource(Weather, '/sensors/weather', '/sensors/weather/<type>')

# sun SVG
@app.route("/sun.svg")
def homepage():
    resp = Response()
    resp.headers['Content-Type'] = 'image/svg+xml'
    resp.data = Sun().get_svg()
    return resp



def run_debug():
    app.run(host="0.0.0.0", debug=True, threaded=True)


def run():
    app.run(host="0.0.0.0", debug=False, threaded=True)


