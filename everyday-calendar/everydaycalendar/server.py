import os
import pickle

from everydaycalendar.calendars import Calendar, Calendars
from everydaycalendar.display import Display
from flask import Flask
from flask_restful import Api, Resource, abort, reqparse

# Declare server "global" variables used in the routes
CALENDARS = Calendars()
CALENDARS["example"] = Calendar(name="Example", color=(51, 153, 255))
DISPLAY = Display()
app = Flask(__name__)
api = Api(app)

class PickleDB:
    """Very simple class to dump the status of the calendar in a pickle file"""
    SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.pkl")

    @staticmethod
    def dump(payload):
        """Save the provided payload"""
        with open(PickleDB.SAVE_PATH, "wb") as f:
            pickle.dump(payload, f)

    @staticmethod
    def load():
        """Retrieve the last dumped payload"""
        def convert(data):
            """Utility function to decode old pickles from python 2"""
            if isinstance(data, bytes):
                return data.decode('ascii')
            elif isinstance(data, dict):
                return dict(map(convert, data.items()))
            elif isinstance(data, tuple):
                return tuple(map(convert, data))
            elif isinstance(data, list):
                return list(map(convert, data))
            else:
                return data

        if os.path.isfile(PickleDB.SAVE_PATH):
            with open(PickleDB.SAVE_PATH, "rb") as f:
                return convert(pickle.load(f, encoding='bytes'))
        return None


class DisplayAPI(Resource):
    """The API ressoure to interract with the displayed state"""
    def get(self, feature=None, param=None):
        out = {
            "brightness": DISPLAY.brightness,
            "calendar": CALENDARS[DISPLAY.calendar_shown].to_dict(format_days=True),
            "switch": "on" if DISPLAY.on else "off"
        }
        return out[feature] if feature in out else out

    def put(self, feature=None, param=None):
        if feature == "calendar":
            DISPLAY.show_calendar(CALENDARS[param])
        elif feature == "brightness":
            DISPLAY.brightness = int(param)
        elif feature == "switch":
            DISPLAY.on = param != "off"
        return self.get(feature)


class CalendarListAPI(Resource):
    """The API ressource that allows you to list the calendars, and create new ones"""
    def get(self):
        out = {}
        for k, v in CALENDARS.items():
            out[k] = v.to_dict(remove_days=True)
            out[k]["active"] = k == DISPLAY.calendar_shown
        return out

    def post(self):
        return CalendarAPI().post()


class CalendarAPI(Resource):
    """API ressource that is used to interract with a calendar"""
    def get(self, calendar_id, raw=False):
        if calendar_id not in CALENDARS:
            abort(404, message="Calendar {} doesn't exist".format(calendar_id))
        return CALENDARS[calendar_id].to_dict(format_days=not raw)

    def delete(self, calendar_id):
        if calendar_id not in CALENDARS:
            abort(404, message="Calendar {} doesn't exist".format(calendar_id))

        CALENDARS.pop(calendar_id)
        if DISPLAY.calendar_shown == calendar_id and len(CALENDARS):
            DISPLAY.show_calendar(list(CALENDARS.values())[0])

        # save_state()
        return CalendarListAPI().get()

    def post(self, calendar_id=None):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('color', type=str)
        args = parser.parse_args()

        # Prepare color
        if args["color"]:
            args["color"] = tuple([int(c) for c in args["color"].split(",")])
            if len(args["color"]) != 3:
                args["color"] = (255, 255, 255)

        calendar = Calendar(id=calendar_id,
                            name=args["name"] or calendar_id,
                            color=args["color"] or (255, 255, 255))
        CALENDARS.insert(calendar)

        # save_state()
        return CalendarListAPI().get()


class DayAPI(Resource):
    """API ressource to interract with a calendar's day"""
    def get(self, calendar_id, year, month, day, status=None):
        if calendar_id not in CALENDARS:
            abort(404, message="Calendar {} doesn't exist".format(calendar_id))
        try:
            return CALENDARS[calendar_id].get_day(int(year), int(month), int(day))
        except IndexError:
            abort(404, message="Unknown day {}/{}/{}".format(day, month, year))

    def put(self, calendar_id, year, month, day, status):
        on = True if status == "on" else False
        CALENDARS[calendar_id].set_day(int(year), int(month), int(day), on=on)
        if DISPLAY.calendar_shown == calendar_id:
            DISPLAY.show_calendar(CALENDARS[calendar_id])
        # save_state()


@app.route("/save")
def save_state():
    PickleDB.dump({"calendars": CALENDARS.dump(), "display": DISPLAY.dump()})
    return "OK"


api.add_resource(DisplayAPI, '/display', '/display/<feature>',
                 '/display/<feature>/<param>')  # feature = on/off/brightness/calendar
api.add_resource(CalendarListAPI, '/calendars')
api.add_resource(CalendarAPI, '/calendars/<calendar_id>')
api.add_resource(DayAPI, '/calendars/<calendar_id>/<year>/<month>/<day>',
                 '/calendars/<calendar_id>/<year>/<month>/<day>/<status>')


@app.route("/")
def home():
    """HTML page to view / debug the calendar in a browser"""
    return DISPLAY.displays[1].get_html_full()


def main():
    # Reload calendar state
    payload = PickleDB.load()
    if isinstance(payload, dict):
        CALENDARS.load(payload["calendars"])
        DISPLAY.load(payload.get("display"), CALENDARS)
    elif isinstance(payload, tuple):  # previous data format
        CALENDARS.load(payload[0])
        if payload[1] in CALENDARS:
            DISPLAY.show_calendar(CALENDARS[payload[1]])
    app.run(debug=False, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    main()
