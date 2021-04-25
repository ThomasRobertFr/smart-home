import datetime
import pickle

import dateutil.parser
import httplib2
import pkg_resources
import pytz
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from ..misc import config as _config
from ..scenarios import Wakeup

config = _config.get().google_calendar


class Calendar:
    """Wrapping API for Google Calandar events that can triggen stuff"""
    def get_credentials(self):
        credentials_path = pkg_resources.resource_filename("smarthome", config.credentials_path)
        store = Storage(credentials_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            client_secret_path = pkg_resources.resource_filename("smarthome", config.client_secret_path)
            flow = client.flow_from_clientsecrets(client_secret_path, config.scopes)
            flow.user_agent = config.app_name
            flow.params['access_type'] = 'offline'
            credentials = tools.run_flow(flow, store)
        return credentials

    def download_calendar(self):
        # Setup API
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        # Show calendars
        # print(service.calendarList().list().execute())

        # Load events
        now = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=config.calendar_id, timeMin=now, maxResults=20, singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def save_events(self, events):
        events_path = pkg_resources.resource_filename("smarthome", config.events_path)
        f = open(events_path, "wb")
        pickle.dump(events, f)
        f.close()

    def read_events(self):
        events_path = pkg_resources.resource_filename("smarthome", config.events_path)
        try:
            f = open(events_path, "rb")
            events = pickle.load(f)
            f.close()
            if not (isinstance(events, list)):
                events = []
            return events
        except:
            return []

    def get_previous(self):
        previous_run_path = pkg_resources.resource_filename("smarthome", config.previous_run_path)
        try:
            with open(previous_run_path, "rb") as f:
                previous = pickle.load(f)
            if not (isinstance(previous, list)):
                previous = []
            return previous
        except:
            return []

    def save_previous(self, previous):
        previous_run_path = pkg_resources.resource_filename("smarthome", config.previous_run_path)
        if len(previous) > 30:
            previous = previous[-30:]
        with open(previous_run_path, "wb") as f:
            pickle.dump(previous, f)

    def process_events(self, events, previous=[]):

        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            start = dateutil.parser.parse(start_str)
            light_start = start - datetime.timedelta(minutes=15)  # start 15 min before event
            now = datetime.datetime.now(pytz.timezone("Europe/Paris"))
            now_minus_25 = now - datetime.timedelta(minutes=25)

            # Event already processed => check next
            if start_str in previous:
                continue

            # Event passed by less than 10 min, let's go!
            if now > light_start > now_minus_25:
                print("Waking up at %s, lighting up" % start_str)
                previous.append(start_str)
                self.save_previous(previous)
                Wakeup().run()

    def update(self):
        events = self.download_calendar()
        self.save_events(events)
        print("events saved")

    def trigger(self):
        events = self.read_events()
        previous = self.get_previous()
        self.process_events(events, previous)
