#!/bin/bash

cd /home/pi/dev/smart-home
uvicorn smarthome.api:app --host 0.0.0.0 --port 5000
