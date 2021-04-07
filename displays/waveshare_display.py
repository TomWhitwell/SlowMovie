from pkgutil import iter_modules
import importlib
from . import VirtualDisplayDevice


class WaveshareDisplay(VirtualDisplayDevice):

    def __init__(self, deviceName):
        super(WaveshareDisplay, self).__init__(f"waveshare.{deviceName}")

        # load the module
        deviceObj = self._load_display_driver(deviceName)

        # create the epd object
        self.device = deviceObj.EPD()

        # set the width and height
        self.width = self.device.width
        self.height = self.device.height

    def _load_display_driver(self, deviceName):
        try:
            # load the given driver module
            driver = importlib.import_module(f"waveshare_epd.{deviceName}")
        except ModuleNotFoundError as mnf:
            # hard stop if driver not
            print(f"{driverName} not found, refer to install instructions")
            exit(2)

        return driver

    @staticmethod
    def get_supported_devices():
        try:
            # load the waveshare library
            waveshareModule = importlib.import_module("waveshare_epd")
        except ModuleNotFoundError as mnf:
            # hard stop if module is not in path
            print("waveshare library not found, refer to install instructions")
            exit(2)

        # return a list of all submodules (device types)
        return [f"waveshare.{s.name}" for s in iter_modules(waveshareModule.__path__) if s.name != 'epdconfig']

    def prepare(self):
        self.device.init()

    def display(self, image, **kwargs):
        self.device.display(self.device.getbuffer(image))

    def sleep(self):
        self.device.sleep()

    def clear(self):
        return True

    def close(self):
        self.device.epdconfig.module_exit()
