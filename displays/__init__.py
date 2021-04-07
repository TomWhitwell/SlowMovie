import importlib

# representation of a display device, impelenting classes should implement these methods
class VirtualDisplayDevice:
    pkg_name = "virtualdevice"
    width = 0
    height = 0
    _device = None
    __device_name = ""

    def __init__(self, deviceName):
        self.device_name = deviceName

    def __str__(self):
        return f"{self.pkg_name}.{self.__device_name}"

    def load_display_driver(self, packageName, className):
        try:
            # load the given driver module
            driver = importlib.import_module(f"{packageName}.{className}")
        except ModuleNotFoundError as mnf:
            # hard stop if driver not
            print(f"{packageName}.{className} not found, refer to install instructions")
            exit(2)

        return driver

    # devices supported by this class
    @staticmethod
    def get_supported_devices():
        raise NotImplementedError

    # run at the top of each update
    def prepare(self):
        return True

    # actual display, PIL image given
    def display(self, image, **kwargs):
        raise NotImplementedError

    # put the display to sleep
    def sleep(self):
        return True

    # clear the display
    def clear(self):
        return True

    # close out the device when the program ends
    def close(self):
        return True
