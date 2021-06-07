"""Run a server with the smart home API on `/api` and the static files on `/`"""
import os

import pkg_resources
import smarthome.api
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(smarthome.api.app.router, prefix="/api")
app.mount("/",
          StaticFiles(directory=pkg_resources.resource_filename("smarthome", "webui"), html=True),
          name="static")


def api_server():
    from uvicorn.main import run
    run(app="smarthome.api:app", host="0.0.0.0", port=5000)


def full_server():
    from uvicorn.main import run
    run(app="smarthome.server:app", host="0.0.0.0", port=5000)
