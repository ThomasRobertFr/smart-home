from flask_restful import Resource
from ..devices import HueLamp, Radio, PowerPlug, Calendar
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
        # "radio": {
        #     "default": True,
        #     "title": "Turn on radio slowly",
        #     "options": {
        #         "delay": 0,
        #         "duration": 300,
        #         "minVolume": 10,
        #         "maxVolume": 30,
        #         #"radio": "gmusic:playlist:865ff4b3-2d34-41da-859b-a084bedb4911"
        #         "radio": "gmusic:radio:7b807d80-5a6a-36d1-9017-9b6ac79371d3"
        #     }
        # },
        # "heating": {
        #     "default": True,
        #     "title": "Start heating",
        #     "config": {
        #         "plug-id": "bathroom-heat"
        #     },
        #     "options": {
        #         "delay": 300,
        #         "duration": 4000
        #     }
        # }
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

        # RADIO

        # time.sleep(self.actions["radio"]["options"]["delay"])
        # if self.should_stop(): return
        # Radio().put(
        #     "wakeSequence",
        #     self.actions["radio"]["options"]
        # )

        # HEATING

        # Start
        # time.sleep(self.actions["heating"]["options"]["delay"])
        # if self.should_stop(): return
        # PowerPlug().put(self.actions["heating"]["config"]["plug-id"], "on")

        # Stop
        # time.sleep(self.actions["heating"]["options"]["duration"])
        # PowerPlug().put(self.actions["heating"]["config"]["plug-id"], "off")

