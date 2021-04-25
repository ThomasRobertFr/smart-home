import subprocess
from typing import Dict

from . import PushButton


class IRRemote(PushButton):
    def __init__(self, remote_id: str, codes: Dict[str, str]):
        self.remote_id = remote_id
        self.codes = codes

    def push(self, command="default"):
        subprocess.call(["irsend", "SEND_ONCE", self.remote_id, self.codes[command]])

    @property
    def commands(self):
        return list(self.codes.keys())
