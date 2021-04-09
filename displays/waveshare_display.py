from pkgutil import iter_modules
import importlib
from . import VirtualDisplayDevice


class WaveshareDisplay(VirtualDisplayDevice):
    pkg_name = 'waveshare_epd'

    def __init__(self, deviceName):
        super(WaveshareDisplay, self).__init__(f"{deviceName}")

        # load the module
        deviceObj = self.load_display_driver(self.pkg_name, deviceName)

        # create the epd object
        self._device = deviceObj.EPD()

        # set the width and height
        self.width = self._device.width
        self.height = self._device.height

    @staticmethod
    def get_supported_devices():
        result = []

        try:
            # load the waveshare library
            waveshareModule = importlib.import_module(WaveshareDisplay.pkg_name)

            # return a list of all submodules (device types)
            result = [f"{WaveshareDisplay.pkg_name}.{s.name}" for s in iter_modules(waveshareModule.__path__) if s.name != 'epdconfig']
        except ModuleNotFoundError:
            # python libs for this might not be installed - that's ok, return nothing
            pass

        return result

    def prepare(self):
        self._device.init()

    def display(self, image):
        self._device.display(self._device.getbuffer(image))

    def sleep(self):
        self._device.sleep()

    def clear(self):
        return True

    def close(self):
        self._device.epdconfig.module_exit()
