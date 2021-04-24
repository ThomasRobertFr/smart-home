"""
import time
import requests
from datetime import datetime, timedelta
import math
from rpi_rf import RFDevice
from ..misc import config as _config
config = _config.get().rf

rfdevice = RFDevice(config.gpio_rx)
rfdevice.enable_rx()

timestamp = None
last_command_id = -1
last_command_time = datetime.now()
while True:
    if rfdevice.rx_code_timestamp != timestamp:
        timestamp = rfdevice.rx_code_timestamp

        if rfdevice.rx_proto != 1:
            continue

        print("DEBUG" + str(rfdevice.rx_pulselength) + " " +str(rfdevice.rx_code))

        # search for the right command
        status = -1
        for i, command in enumerate(config.commands):
            # pulse, on, off, [type, id]
            if math.fabs(command[0] - rfdevice.rx_pulselength) < 5 and math.fabs(command[1] - rfdevice.rx_code) < 1:
                status = 1
                break
            if math.fabs(command[0] - rfdevice.rx_pulselength) < 5 and math.fabs(command[2] - rfdevice.rx_code) < 1:
                status = 0
                break

        # command found, try to do something
        if status != -1:
            print("Received %s %d" % (command, status))

            # avoid multiple calls
            if last_command_id == i*2+status and datetime.now() - last_command_time < timedelta(seconds=5):
                continue
            last_command_id = i*2+status
            last_command_time = datetime.now()

            # do something
            #print("%s st=%d, code=%d, pulse=%d" % (command, status, rfdevice.rx_code, rfdevice.rx_pulselength))
            if command[3] == "plug":
                requests.put("http://raspi/api/devices/power-plug/%s/%s" % (command[4], "on" if status == 1 else "off"))
            if command[3] == "put":
                url = command[4] if status == 1 else command[5]
                if "scenarios" in url:
                    time.sleep(1.5)
                requests.put("http://raspi/api/%s" % url)

    time.sleep(0.01)
"""

