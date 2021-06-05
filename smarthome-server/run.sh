#!/bin/bash

cd "$(dirname "$0")"
uvicorn smarthome.api:app --host 0.0.0.0 --port 5000
