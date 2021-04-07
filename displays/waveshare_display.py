from pkgutil import iter_modules
import importlib
from . import VirtualDisplayDevice


class WaveshareDisplay(VirtualDisplayDevice):

    def __init__(self, deviceName):
        super(WaveshareDisplay, self).__init__(f"waveshare.{deviceName}")

        # load the module
        deviceObj = self.load_display_driver('waveshare_epd', deviceName)

        # create the epd object
        self.device = deviceObj.EPD()

        # set the width and height
        self.width = self.device.width
        self.height = self.device.height


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
