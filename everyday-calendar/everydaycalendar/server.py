import os
import re
import sys
from copy import deepcopy
import cPickle as pickle
import unicodedata
import time
from datetime import datetime

import numpy as np
from neopixel import Color, Adafruit_NeoPixel
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource


app = Flask(__name__)
api = Api(app)

SAVE_PATH = "/home/pi/calendar/data.pkl"

# Create NeoPixel object with appropriate configuration.
LED_COUNT = 366  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
STRIP = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
STRIP.begin()

START_YEAR = 2020  # first year for which we record calendars
NB_DAYS_PER_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DAYS_PER_YEAR = sum(NB_DAYS_PER_MONTH)
EXPECTED_CALENDAR_LENGHT = DAYS_PER_YEAR * (datetime.now().year - START_YEAR + 1)
DAYS = []
for i, nb_j in enumerate([31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]):
    for j in range(nb_j):
        DAYS.append("%02d-%02d" % (i + 1, j + 1))
def get_day_index(year, month, day):
    index = (year - START_YEAR) * DAYS_PER_YEAR  # e.g. 2020 -> 365
    index += sum(NB_DAYS_PER_MONTH[:month - 1])  # e.g. march -> 31 (jan) + 29 (feb)
    index += day - 1
    return index

CALENDARS = {
    'sober': {'name': 'Sober', "color": (51, 153, 255), "days": {"02-08", "01-04", "01-08"}},
    'derby': {'name': 'Derby', "color": (51, 204, 51), "days": {"02-20", "01-04", "01-08"}},
}
DISPLAY_CURRENT = list(CALENDARS.keys())[0]
DISPLAY_CURRENT_BRIGHTNESS = LED_BRIGHTNESS
DISPLAY_CURRENT_ON = True

# Reload saved state
if os.path.isfile(SAVE_PATH):
    with open(SAVE_PATH, "rb") as f:
        CALENDARS, DISPLAY_CURRENT = pickle.load(f)

# Ensure the days field in the calendar has the correct shape, enlage if needed
for calendar in CALENDARS.values():
    if len(calendar["days"]) < EXPECTED_CALENDAR_LENGHT:
        assert calendar["days"].shape[1] == 3
        calendar["days"] = np.pad(calendar["days"],
                                [[0, EXPECTED_CALENDAR_LENGHT - calendar["days"].shape[0]], [0, 0]])


@app.route("/save")
def save_state():
    with open(SAVE_PATH, "wb") as f:
        pickle.dump((CALENDARS, DISPLAY_CURRENT), f)
    return "OK"


class Display(Resource):
    def get(self, feature=None, param=None):
        if feature == "brightness":
            return DISPLAY_CURRENT_BRIGHTNESS
        elif feature == "calendar":
            return Calendar().get(DISPLAY_CURRENT)
        elif feature == "switch":
            return "on" if DISPLAY_CURRENT_ON else "off"
        else:
            return {
                "brightness": DISPLAY_CURRENT_BRIGHTNESS,
                "calendar": Calendar().get(DISPLAY_CURRENT),
                "switch": "on" if DISPLAY_CURRENT_ON else "off"
            }

    def put(self, feature=None, param=None):
        if feature == "calendar":
            return self.set_calendar(param)
        elif feature == "brightness":
            return self.set_brightness(int(param))
        elif feature == "switch":
            return self.set_switch(param)

    def set_switch(self, value):
        global DISPLAY_CURRENT_ON
        global STRIP

        DISPLAY_CURRENT_ON = value != "off"
        if DISPLAY_CURRENT_ON:
            return self.set_brightness(DISPLAY_CURRENT_BRIGHTNESS)
        else:
            return self.set_brightness(0, save=False)

    def set_brightness(self, value, save=True):
        global DISPLAY_CURRENT_BRIGHTNESS
        global STRIP

        value = max(0, min(255, int(value)))
        if save:
            DISPLAY_CURRENT_BRIGHTNESS = value
        STRIP = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, value)
        STRIP.begin()
        return self.refresh_display()

    def set_calendar(self, calendar_id):
        global DISPLAY_CURRENT
        if calendar_id is not None:
            Calendar().get(calendar_id, raw=True)  # Check if exists
            DISPLAY_CURRENT = calendar_id
        return self.refresh_display()

    def refresh_display(self):
        calendar = Calendar().get(DISPLAY_CURRENT, raw=True)
        current_year = datetime.now().year
        if not DISPLAY_CURRENT_ON:
            self.hide_grid()
        else:
            # Previous year
            month_bounds = [get_day_index(current_year - 1, month + 1, 1) for month in range(12)]
            month_bounds += [get_day_index(current_year, month + 1, 1) for month in range(12)]
            month_bounds.append(get_day_index(current_year + 1, 1, 1))
            months_colors = []
            for start, end in zip(month_bounds[:12], month_bounds[1:]):
                days = calendar["days"][start:end].astype(np.uint32) / 5
                days = days[:, 1] * (2 ** 16) + (days[:, 0] * 2 ** 8) + days[:, 2]
                months_colors.append(days)
            for i, start, end in zip(range(12), month_bounds[12:24], month_bounds[13:]):
                days = calendar["days"][start:end].astype(np.uint32)
                days = days[:, 1] * (2 ** 16) + (days[:, 0] * 2 ** 8) + days[:, 2]
                months_colors[i] = np.maximum(months_colors[i], days)
            self.show_grid(months_colors)
        return Calendar().get(DISPLAY_CURRENT)

    @staticmethod
    def hide_grid():
        for i in range(LED_COUNT):
            STRIP.setPixelColor(i, 0)
        STRIP.show()

    @staticmethod
    def show_grid(color_grid):
        order = -1
        i = 0
        for month_i in reversed(range(12)):
            for day_color in color_grid[month_i][::order]:
                STRIP.setPixelColor(i, int(day_color))
                i += 1
            order = order * -1
        STRIP.show()


class CalendarList(Resource):
    def get(self):
        calendars = deepcopy(CALENDARS)
        for k, v in calendars.items():
            del v["days"]
            v["id"] = k
            v["active"] = k == DISPLAY_CURRENT
        return calendars

    def post(self):
        return Calendar().post()


parser = reqparse.RequestParser()
parser.add_argument('name', type=str)
parser.add_argument('color', type=str)


class Calendar(Resource):
    def get(self, calendar_id, raw=False):
        if calendar_id not in CALENDARS:
            abort(404, message="Calendar {} doesn't exist".format(calendar_id))
        calendar = CALENDARS[calendar_id].copy()
        calendar["id"] = calendar_id
        if not raw:
            calendar["current_year"] = str(datetime.now().year)
            np_days = calendar["days"]
            calendar["days"] = {}
            for year in range(START_YEAR, datetime.now().year + 1):
                calendar["days"][str(year)] = []
                for month, nb_days in zip(range(12), NB_DAYS_PER_MONTH):
                    month_days = np_days[
                         get_day_index(year, month + 1, 1):get_day_index(year, month + 1, nb_days)
                     ].max(axis=1).clip(0, 1).tolist()
                    calendar["days"][str(year)].append(month_days)
        return calendar

    def slugify(self, value):
        if sys.version_info.major == 2:
            if not isinstance(value, unicode):
                value = unicode(value)
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        if sys.version_info.major == 2:
            value = unicode(value)
        return re.sub(r'[-\s]+', '-', value)

    def name_to_id(self, name, create_new=False):
        id = self.slugify(name)
        if not create_new:
            return id
        add = ""
        while id + str(add) in CALENDARS:
            if add == "":
                add = 1
            else:
                add += 1
        return id + str(add)

    def delete(self, calendar_id):
        global DISPLAY_CURRENT
        if calendar_id not in CALENDARS:
            abort(404, message="Calendar {} doesn't exist".format(calendar_id))

        del CALENDARS[calendar_id]
        if DISPLAY_CURRENT == calendar_id:
            DISPLAY_CURRENT = list(CALENDARS.keys())[0]
            Display().refresh_display()

        # save_state()
        return CalendarList().get()

    def post(self, calendar_id=None):
        args = parser.parse_args()
        if calendar_id is None:
            calendar_id = self.name_to_id(args.get("name", "default"), create_new=True)

        # Prepare color
        if args["color"]:
            args["color"] = tuple([int(c) for c in args["color"].split(",")])
            if len(args["color"]) != 3:
                args["color"] = (255, 255, 255)

        if calendar_id not in CALENDARS:
            CALENDARS[calendar_id] = {
                "id": calendar_id,
                "name": calendar_id,
                "color": (255, 255, 255),
                "days": np.zeros((EXPECTED_CALENDAR_LENGHT, 3), dtype=np.uint8)
            }

        if args["name"]:
            CALENDARS[calendar_id]["name"] = args["name"]
        if args["color"]:
            CALENDARS[calendar_id]["color"] = args["color"]

        # save_state()
        Display().refresh_display()
        return CalendarList().get()


class Day(Resource):
    def get(self, calendar_id, year, month, day, status=None):
        if calendar_id not in CALENDARS:
            abort(404, message="Calendar {} doesn't exist".format(calendar_id))
        index = get_day_index(int(year), int(month), int(day))
        try:
            return CALENDARS[calendar_id]["days"][index].tolist()
        except IndexError:
            abort(404, message="Unknown day {}/{}/{}".format(day, month, year))

    def put(self, calendar_id, year, month, day, status):
        index = get_day_index(int(year), int(month), int(day))
        add = True if status == "on" else False
        if add:
            CALENDARS[calendar_id]["days"][index] = CALENDARS[calendar_id]["color"]
        else:
            CALENDARS[calendar_id]["days"][index] = 0
        Display().refresh_display()
        # save_state()
        return


api.add_resource(Display, '/display', '/display/<feature>', '/display/<feature>/<param>')  # feature = on/off/brightness/calendar
api.add_resource(CalendarList, '/calendars')
api.add_resource(Calendar, '/calendars/<calendar_id>')
api.add_resource(Day, '/calendars/<calendar_id>/<year>/<month>/<day>', '/calendars/<calendar_id>/<year>/<month>/<day>/<status>')

if __name__ == '__main__':
    Display().refresh_display()
    app.run(debug=False, host="0.0.0.0", port=5000)
