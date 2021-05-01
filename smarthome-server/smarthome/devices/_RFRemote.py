try:
    from rpi_rf import RFDevice
except:
    import warnings
    warnings.warn("Lib rpi_rf not found, using mock for testing on a local machine")
    class RFDevice:
        def __init__(self, tx): pass
        def enable_tx(self): pass
        def tx_code(self, code, duration, pulse): print(f"Sending code {pulse}/{code}")

from smarthome.devices import Switch
from smarthome.misc import config as _config

config = _config.get().rf

RFDEVICE = RFDevice(config.gpio_tx)
RFDEVICE.enable_tx()


class RFRemote(Switch):
    def __init__(self, id: str, idx: int, remote: str):
        super().__init__(id, idx)
        if remote not in config.remotes:
            raise ValueError(f"Unkown remote {remote}, available are {list(config.remotes.keys())}")
        self.pulse = config.remotes[remote][0]
        self.code_on = config.remotes[remote][1]
        self.code_off = config.remotes[remote][2]

    def on(self):
        RFDEVICE.tx_code(self.code_on, 1, self.pulse)

    def off(self):
        RFDEVICE.tx_code(self.code_off, 1, self.pulse)
