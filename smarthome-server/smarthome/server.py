from fastapi import FastAPI, Response

from .devices import Devices
from .scenarios import Scenarios
from .triggers import Calendar
from .sensors import Sun, Weather


app = FastAPI()
DEVICES = Devices()
SCENARIOS = Scenarios()


@app.get("/devices")
def get_devices():
    return DEVICES.list_dict


@app.get("/scenarios")
def get_devices():
    return SCENARIOS.list_dict


# Could be funny to do something like that, to try
# for device in devices_list:
#     @app.get("/devices-by-id/"+device["id"]+"/{state}")


@app.get("/devices-by-id/{id}")
def get_devices_by_id(id: str):
    return DEVICES.by_id_dict[id]


@app.get("/devices-by-idx/{idx}")
def get_devices_by_idx(idx: int):
    return DEVICES.by_idx_dict[idx]


@app.put("/devices-by-id/{id}/{state}")
def put_devices_by_id(id: str, state: str):
    DEVICES[id].put(state)


@app.put("/devices-by-idx/{idx}/{state}")
def put_devices_by_idx(idx: int, state: str):
    DEVICES[idx].put(state)


@app.put("/scenarios-by-id/{id}")
def put_scenarios_by_id(id: str):
    SCENARIOS.by_id[id].run()


@app.put("/scenarios-by-idx/{idx}")
def put_scenarios_by_idx(idx: int):
    SCENARIOS.by_idx[idx].run()


@app.put("/devices-and-scenarios-by-id/{id}/{state}")
def put_devices_or_scenarios_by_id(id: str, state: str):
    if id in DEVICES:
        DEVICES[id].put(state)
    elif state == "on":
        SCENARIOS[id].run()


@app.put("/devices-and-scenarios-by-idx/{idx}/{state}")
def put_devices_or_scenarios_by_idx(idx: int, state: str):
    if idx in DEVICES:
        DEVICES[idx].put(state)
    elif state == "on":
        SCENARIOS[idx].run()


@app.get("/sensors/weather")
@app.get("/sensors/weather/{query}")
def get_weather(query: Weather.Query = Weather.Query.forecast):
    return Weather.get(query)


@app.get("/sensors/sun.svg")
def sun_svg():
    return Response(content=Sun().svg(), media_type='image/svg+xml')


@app.get("/triggers/calendar/update")
def calendar_update():
    return Calendar().update()


@app.get("/triggers/calendar/trigger")
def calendar_update():
    return Calendar().trigger()

# Watering
# api.add_resource(WateringSensors, '/devices/watering')
# api.add_resource(WateringSensor, '/devices/watering/<id>', '/devices/watering/<id>/<verb>')
