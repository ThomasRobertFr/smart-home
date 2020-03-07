from flask_restful import Resource
from ..devices import PowerPlug, RemotePilotWire, Calendar
from ..sensors import State


class Arrive(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs on",
            "config": {
                "plug-ids": ["main-lamp", "plasma-lamp", "desk", "phone-charger"]
            }
        },
        "heating": {
            "default": True,
            "title": "Turn heating on"
        }
    }

    def get(self):
        return self.actions

    def put(self):
        print("=== ARRIVE HOME ===")

        State().put("home")

        # HEATING ON
        RemotePilotWire().put("on")

        Calendar().put("brightness", "10")
        Calendar().put("switch", "on")

        # PLUGS ON
        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "on")



