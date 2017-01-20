from flask_restful import Resource
import requests
import time
from flask import request
from ..misc import config as _config
config = _config.get().rcp

class Radio(Resource):

    request_id = 1

    def make_request(self, method, params={}, debug_title="unkn req"):
        r = requests.post(config.url, json={
            "method": method,
            "jsonrpc": "2.0",
            "params": params,
            "id": Radio.request_id
        })
        Radio.request_id += 1
        print("%s: %s" % (debug_title, r.status_code))
        return r

    def clear_queue(self):
        self.make_request("core.tracklist.clear", debug_title="clear queue")

    def queue_radio(self, radio_uri):
        r = self.make_request("core.library.browse", {"uri": radio_uri}, "get tracks from %s" % radio_uri)
        tracks = list(map(lambda x: x['uri'], r.json()['result']))
        self.make_request("core.tracklist.add", {"uris": tracks}, debug_title="queue tracks")
        self.make_request("core.playback.play", debug_title="play")

    def play(self):
        self.make_request("core.playback.play", debug_title="play")

    def pause(self):
        self.make_request("core.playback.pause", debug_title="pause")

    def next(self):
        self.make_request("core.playback.next", debug_title="next")

    def previous(self):
        self.make_request("core.playback.previous", debug_title="previous")

    def set_volume(self, volume):
        self.make_request("core.mixer.set_volume", {"volume": volume}, debug_title="volume = %d" % volume)

    def fade_volume(self, start_volume=1, end_volume=30, duration=300, fade_interval=3):
        for i in range(0, duration + 1, fade_interval):
            volume = int(start_volume + i * float(end_volume - start_volume) / duration)
            self.make_request("core.mixer.set_volume", {"volume": volume}, debug_title="volume = %d" % volume)
            time.sleep(fade_interval)

    def put(self, action, data=None):
        if data is None:
            data = request.json
        if data is None:
            data = {}

        if action == "clearQueue":
            self.clear_queue()
        if action == "queueRadio":
            radio = data.get("radio", "gmusic:radio:7b807d80-5a6a-36d1-9017-9b6ac79371d3")
            self.queue_radio(radio)

        if action == "play":
            self.play()
        if action == "pause":
            self.pause()
        if action == "next":
            self.next()
        if action == "previous":
            self.previous()

        if action == "setVolume":
            volume = data.get("volume", 1)
            self.set_volume(volume)
        if action == "fadeVolume":
            start_volume = data.get("startVolume", 1)
            end_volume = data.get("endVolume", 30)
            duration = data.get("duration", 300)
            fade_interval = data.get("fadeInterval", 3)
            self.fade_volume(start_volume, end_volume, duration, fade_interval)

        if action == "wakeSequence":
            radio = data.get("radio", "gmusic:radio:7b807d80-5a6a-36d1-9017-9b6ac79371d3")
            start_volume = data.get("startVolume", 1)
            end_volume = data.get("endVolume", 30)
            duration = data.get("duration", 300)
            fade_interval = data.get("fadeInterval", 3)
            self.set_volume(1)
            self.clear_queue()
            self.queue_radio(radio)
            self.fade_volume(start_volume, end_volume, duration, fade_interval)


