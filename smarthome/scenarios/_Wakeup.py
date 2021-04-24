from flask_restful import Resource
from ..devices import HueLamp, PowerPlug, Calendar
from ..sensors import State, Threads
import time


class WakeUp(Resource, Threads.Stoppable):

    actions = {
        "light": {
            "default": True,
            "title": "Turn on lamp slowly",
            "config": {
                "hue-id": 1
            },
            "options": {
                "delay": 0,
                "duration": 600
            }
        },
    }

    def get(self):
        return self.actions

    def put(self):
        print("== Run wakeup sequence ==")
        self.init_stop("Wake up")

        State().put("home")

        # LIGHT

        # Initial color
        time.sleep(self.actions["light"]["options"]["delay"])
        HueLamp().send(
            self.actions["light"]["config"]["hue-id"],
            {"on": True, "bri": 0, "xy": [0.674, 0.322], "transitiontime": 0})

        # Start transition
        time.sleep(1.5)
        HueLamp().send(
            self.actions["light"]["config"]["hue-id"],
            {"on": True, "bri": 254, "xy": [0.4974, 0.4152], "transitiontime": self.actions["light"]["options"]["duration"] * 10})

        PowerPlug().put(self.actions["heating"]["config"]["plug-id"], "on")

        # CALENDAR
        Calendar().put("brightness", "10")
        Calendar().put("switch", "on")
