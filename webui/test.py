 #!/usr/bin/python
# -*- coding: utf8 -*-

import requests
import re
import urllib
import subprocess
import os

# Weather forecast

forecast = u"Partiellement nuageux. Maximales : 6 ºC. Vents NNO soufflant de 10 à 15 km/h."
r = requests.get("http://api.wunderground.com/api/3fe0da5755741878/forecast/lang:FR/q/France/Paris%2005%20Pantheon.json")
forecast = r.json()["forecast"]["txt_forecast"]["forecastday"][0]["fcttext_metric"]
forecast = forecast.replace(u"ºC", u"degrés")
forecast = forecast.replace(u"km/h", u"kilomètres-heure")
forecast = u"La météo annonce "+forecast
#print forecast

# Velib slots
# stations: https://api.jcdecaux.com/vls/v1/stations?contract=Paris&apiKey=fc028686bf11528594e3b870648f4b695614ee99

velib = u"Concernant les vélibs. "

def velibSentence(data, name):
    out = u""
    if data["status"] != "OPEN":
        out += u"%s est fermée. " % name
    elif data["available_bikes"] >= 5:
        out += u"Il reste %d vélos à %s. " % (data["available_bikes"], name)
    elif data["available_bikes"] > 0:
        out += u"Attention ! Il n'y a plus que %d vélos à %s. " % (data["available_bikes"], name)
    else:
        out += u"Attention ! Il n'y a pas de vélos à %s. " % name
    return out

# Mouffetard 05026
r = requests.get("https://api.jcdecaux.com/vls/v1/stations/05026?contract=Paris&apiKey=fc028686bf11528594e3b870648f4b695614ee99").json()
velib += velibSentence(r, u"la station Mouffetard")

# Monge 05024
if r["status"] != "OPEN" or r["available_bikes"] < 5:
    r = requests.get("https://api.jcdecaux.com/vls/v1/stations/05024?contract=Paris&apiKey=fc028686bf11528594e3b870648f4b695614ee99")
    velib += velibSentence(r.json(), u"la station place Monge")

# Place Jussieu 05023
# Jussieu 05021
# Lacepede 05031
pj = requests.get("https://api.jcdecaux.com/vls/v1/stations/05023?contract=Paris&apiKey=fc028686bf11528594e3b870648f4b695614ee99").json()
j = requests.get("https://api.jcdecaux.com/vls/v1/stations/05021?contract=Paris&apiKey=fc028686bf11528594e3b870648f4b695614ee99").json()
l = requests.get("https://api.jcdecaux.com/vls/v1/stations/05031?contract=Paris&apiKey=fc028686bf11528594e3b870648f4b695614ee99").json()

if pj["available_bike_stands"] > 4:
    velib += u"Je te conseille la station à l'entrée de Jussieu. "
elif l["available_bike_stands"] > 4:
    velib += u"Je te conseille la station Lacépaide. "
elif j["available_bike_stands"] > 4:
    velib += u"Je te conseille la station Jussieu. "
else:
    velib += u"Toutes les stations au travail sont assez pleines."
velib += u"Il y a %d places à l'entrée, %d places à Lacépaide et %d places à Jussieu." % (pj["available_bike_stands"], l["available_bike_stands"], j["available_bike_stands"])

#print velib

#urllib.urlretrieve("http://www.voxygen.fr/sites/all/modules/voxygen_voices/assets/proxy/index.php?method=redirect&%s&voice=Bronwen&ts=1480362849466" % urllib.urlencode({"text":forecast}), "/tmp/tmp1.mp3")
#urllib.urlretrieve("http://www.voxygen.fr/sites/all/modules/voxygen_voices/assets/proxy/index.php?method=redirect&%s&voice=Bronwen&ts=1480362849466" % urllib.urlencode({"text":velib}), "/tmp/tmp2.mp3")
#urllib.urlretrieve("http://www.voxygen.fr/sites/all/modules/voxygen_voices/assets/proxy/index.php?method=redirect&%s&voice=Bronwen&ts=1480362849466" % urllib.urlencode({"text":"I'm turning of the radio now. Have a nice day."}), "/tmp/tmp3.mp3")

urllib.urlretrieve("http://www.voxygen.fr/sites/all/modules/voxygen_voices/assets/proxy/_index.php?method=redirect&%s&voice=Loic&ts=1480362849466" % urllib.urlencode({"text":unicode(forecast+u" "+velib+u" Bonne journée !").encode('utf-8')}), "/var/lib/mopidy/media/tmp.mp3")

# Play with mopidy, stop the radio at the same time if running
RPC_URL = "http://raspi:6680/mopidy/rpc"
REQ_ID = 1

def make_request(method, params = {}, debug_title = "unkn req"):
    global REQ_ID
    r = requests.post(RPC_URL, json={
      "method": method,
      "jsonrpc": "2.0",
      "params": params,
      "id": REQ_ID
    })
    REQ_ID = REQ_ID + 1
    print("%s: %s" % (debug_title, r.status_code))
    return r

make_request("core.tracklist.clear", debug_title="clear queue")
make_request("core.mixer.set_volume", {"volume": 100}, debug_title="volume = 100")
make_request("core.tracklist.add", {"uri": "file:///var/lib/mopidy/media/tmp.mp3"}, debug_title="queue tracks")
make_request("core.playback.play", debug_title="play")
