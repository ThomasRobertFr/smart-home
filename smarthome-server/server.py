"""Run a server with the smart home API on `/api` and the static files on `/`"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import smarthome.api

app = FastAPI()

app.include_router(smarthome.api.app.router, prefix="/api")
app.mount("/", StaticFiles(directory="webui", html=True), name="static")
