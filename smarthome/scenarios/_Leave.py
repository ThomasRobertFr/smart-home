from flask_restful import Resource
from ..devices import Radio, PowerPlug, RemotePilotWire, NAS
from ..sensors import State


class Leave(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs off",
            "config": {
                "plug-ids": ["main-lamp", "bedside-lamp", "plasma-lamp", "starwars-lamp", "desk", "bathroom-heat"]
            }
        },
        "radio": {
            "default": True,
            "title": "Turn radio off"
        },
        "heating": {
            "default": True,
            "title": "Turn heating off"
        }
    }

    def get(self):
        return self.actions

    def put(self):

        State().put("away")

        # HEATING OFF
        RemotePilotWire().put("off")

        # RADIO OFF
        Radio().put("clearQueue")

        # NAS OFF
        NAS().put("off")

        # PLUGS OFF
        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "off")



