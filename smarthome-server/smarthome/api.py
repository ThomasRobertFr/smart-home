import traceback

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from smarthome import watering

from .devices import Devices
from .scenarios import Scenarios
from .sensors import Sun, Weather
from .triggers import Calendar

app = FastAPI()
DEVICES = Devices()
SCENARIOS = Scenarios()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/devices", tags=["devices"])
def get_devices():
    return DEVICES.list_dict


@app.get("/scenarios", tags=["scenarios"])
def get_devices():
    return SCENARIOS.list_dict


@app.get("/devices-by-id/{id}", tags=["devices"])
def get_devices_by_id(id: str):
    return DEVICES.by_id_dict[id]


@app.get("/devices-by-idx/{idx}", tags=["devices"])
def get_devices_by_idx(idx: int):
    return DEVICES.by_idx_dict[idx]


@app.put("/devices-by-id/{id}/{state}", tags=["devices"])
def put_devices_by_id(id: str, state: str):
    DEVICES[id].put(state)


@app.put("/devices-by-idx/{idx}/{state}", tags=["devices"])
def put_devices_by_idx(idx: int, state: str):
    DEVICES[idx].put(state)


@app.put("/scenarios-by-id/{id}", tags=["scenarios"])
def put_scenarios_by_id(id: str):
    SCENARIOS.by_id[id].run()


@app.put("/scenarios-by-idx/{idx}", tags=["scenarios"])
def put_scenarios_by_idx(idx: int):
    SCENARIOS.by_idx[idx].run()


@app.put("/devices-and-scenarios-by-id/{id}/{state}", tags=["devices", "scenarios"])
def put_devices_or_scenarios_by_id(id: str, state: str):
    if id in DEVICES:
        DEVICES[id].put(state)
    elif state == "on":
        SCENARIOS[id].run()


@app.put("/devices-and-scenarios-by-idx/{idx}/{state}", tags=["devices", "scenarios"])
def put_devices_or_scenarios_by_idx(idx: int, state: str):
    if idx in DEVICES:
        DEVICES[idx].put(state)
    elif state == "on":
        SCENARIOS[idx].run()


@app.get("/sensors/weather", tags=["sensors"])
@app.get("/sensors/weather/{query}", tags=["sensors"])
def get_weather(query: Weather.Query = Weather.Query.forecast):
    return Weather.get(query)


@app.get("/sensors/sun.svg", tags=["sensors"])
def sun_svg():
    return Response(content=Sun().svg(), media_type='image/svg+xml')


@app.get("/triggers/calendar/update", tags=["triggers"])
def calendar_update():
    return Calendar().update()


@app.get("/triggers/calendar/trigger", tags=["triggers"])
def calendar_update():
    return Calendar().trigger()


app.include_router(watering.api.router)


@app.exception_handler(Exception)
def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={
            "error": str(exc),
            "trace": traceback.format_tb(exc.__traceback__)
        },
    )
