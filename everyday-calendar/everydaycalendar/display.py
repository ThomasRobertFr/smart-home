"""In this module, we have the ways to display the current state of the calendar, either physically
using `neopixel` to interract with an LED strip; or virtually by generating an HTML view of the
calendar.

Both displays have the same interface
"""
import abc
import os.path
import warnings
from datetime import datetime
from typing import List

from everydaycalendar.calendars import (DAYS_PER_YEAR, NB_DAYS_PER_MONTH, Calendar, Calendars)


class DisplayInterface(metaclass=abc.ABCMeta):
    """Abstract interface for a display of the calendar"""
    @abc.abstractmethod
    def set_brightness(self, value):
        pass

    @abc.abstractmethod
    def set_day(self, month, day, rgb):
        pass

    @abc.abstractmethod
    def show(self):
        pass


class HTMLDisplay(DisplayInterface):
    """Class that handle the HTML view of a currently shown calendar. It is useful to work on the
    code on a local machine that does not have a real led strip. It should be able to simulate the
    LED strip.
    """
    file_with_css = None
    file = None

    def __init__(self):
        self.brightness = 10
        self.rgbs = [[(0, 0, 0) for _ in range(n)] for n in NB_DAYS_PER_MONTH]

    def set_brightness(self, value):
        self.brightness = value
        self.show()

    def set_day(self, month, day, rgb):
        self.rgbs[month][day] = tuple(rgb)

    def get_html(self):
        out = """<table>
          <tr class="months">
            <td></td>
            <td>J</td><td>F</td><td>M</td><td>A</td><td>M</td><td>J</td>
            <td>J</td><td>A</td><td>S</td><td>O</td><td>N</td><td>D</td>
          </tr>
        """
        for d in range(max(NB_DAYS_PER_MONTH)):
            out += '<tr><td class="day_title">{}</td>'.format(d + 1)
            for m in range(len(NB_DAYS_PER_MONTH)):
                out += '<td>'
                if d < len(self.rgbs[m]):
                    r, g, b = self.rgbs[m][d]
                    out += '<span class="circle" id="calendar_day_{day:02d}-{month:02d}" ' \
                           'style="background-color: rgb({r}, {g}, {b});"></span>' \
                           .format(day=d + 1, month=m + 1, r=r, g=g, b=b)
                out += '</td>'
            out += '</tr>'
        out += '</table> Brightness = {}'.format(self.brightness)
        return out

    def get_html_full(self):
        with open(os.path.join(os.path.dirname(__file__), "template.html"), "r") as f:
            page = f.read()
        return page.replace("{{table}}", self.get_html())

    def show(self):
        if self.file:
            with open(os.path.join(os.path.dirname(__file__), "..", self.file), "w") as f:
                f.write(self.get_html_full())


class LedStrip(DisplayInterface):
    """Real display interracting with the LED strip. The key thing to handle here is to properly map
    each day to the right index in the LED strip.
    """
    def __init__(self):
        from board import D18  # Led strip pin
        from neopixel import NeoPixel
        self.strip = NeoPixel(D18, DAYS_PER_YEAR, auto_write=False)

        # prepare a mapping from (month, day) to the position in the led strip
        self.day_month_to_index = {}
        order = -1
        i = 0
        # iterate on all months starting from december
        for month_i in reversed(range(12)):
            # iterate on days from beggining or end depending on month
            for day_i in range(NB_DAYS_PER_MONTH[month_i])[::order]:
                self.day_month_to_index[(month_i, day_i)] = i
                i += 1
            order = order * -1
        for i in range(DAYS_PER_YEAR):
            self.strip[i] = 0
        self.show()

    def set_brightness(self, value):
        self.strip.brightness = value / 255

    def set_day(self, month, day, rgb):
        """Set the color for a given date (month and day starting at 0) to given RGB"""
        i = self.day_month_to_index[(month, day)]
        self.strip[i] = [int(_) for _ in rgb]

    def show(self):
        self.strip.show()


class Display:
    """A class to store the state of the display. Should be instanciated once."""
    def __init__(self):
        self._on = True
        self._brightness = 10
        self._calendar_shown = None
        self.displays: List[DisplayInterface] = [HTMLDisplay()]
        try:
            self.displays.append(LedStrip())
        except ModuleNotFoundError:
            warnings.warn("neopixel module not available")

    @property
    def calendar_shown(self):
        return self._calendar_shown

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        self._on = bool(value)
        for strip in self.displays:
            strip.set_brightness(self._brightness if self.on else 0)
            strip.show()

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = max(0, min(255, int(value)))
        for strip in self.displays:
            strip.set_brightness(self._brightness if self.on else 0)
            strip.show()

    def show_calendar(self, calendar: Calendar):
        """Display a specific calendar"""
        self._calendar_shown = calendar.id

        days_dict = calendar.format_days(binary=False)  # Dict[str, List[List[(int, int, int)]]]
        current_year = days_dict[str(datetime.now().year)]
        previous_year = days_dict[str(datetime.now().year - 1)]

        for month_i, (month_current, month_previous) in enumerate(zip(current_year, previous_year)):
            for day_i, (day_color_current, day_color_previous) in \
                    enumerate(zip(month_current, month_previous)):
                if any(day_color_current):  # use current year if lit
                    day_color = day_color_current
                else:  # use previous year otherwise but divide brightness by 5
                    day_color = [_ / 5 for _ in day_color_previous]

                for strip in self.displays:
                    strip.set_day(month_i, day_i, day_color)

        for strip in self.displays:
            strip.show()

    def dump(self):
        return {
            "calendar_shown": self.calendar_shown,
            "brightness": self.brightness,
            "on": self.on,
        }

    def load(self, payload: dict, calendars: Calendars):
        self.on = payload.get("on", True)
        if payload.get("calendar_shown") in calendars:
            self.show_calendar(calendars[payload["calendar_shown"]])
        if "brightness" in payload:
            self.brightness = int(payload["brightness"])
