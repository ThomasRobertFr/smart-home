"""Run a server with the smart home API on `/api` and the static files on `/`"""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import smarthome.api

app = FastAPI()

app.include_router(smarthome.api.app.router, prefix="/api")
app.mount("/",
          StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../webui"), html=True),
          name="static")


def api_server():
    from uvicorn.main import run
    run(app="smarthome.api:app", host="0.0.0.0", port=5000)


def full_server():
    from uvicorn.main import run
    run(app="smarthome.server:app", host="0.0.0.0", port=5000)
