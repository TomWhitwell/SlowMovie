import importlib


# VirtualDisplayDevice is a wrapper class for a device, or family of devices, that all use the same display code
# New devices should extend this class and implement the, at a minimum, the following:
#
# pkg_name = set this to the package name of the concrete class
# width = width of display, can set in __init__
# height = height of display, can set in __init__
# get_supported_devices = must return a list of supported devices for this class in the format {pkgname.devicename}
# display = performs the action of writing the image to the display
class VirtualDisplayDevice:
    pkg_name = "virtualdevice"  # the package name of the concrete class
    width = 0   # width of display
    height = 0  # height of display
    _device = None  # concrete device class, initialize in __init__
    __device_name = ""  # name of this device

    def __init__(self, deviceName):
        self.__device_name = deviceName

    def __str__(self):
        return f"{self.pkg_name}.{self.__device_name}"

    # helper method to load a concrete display object based on the package and class name
    def load_display_driver(self, packageName, className):
        try:
            # load the given driver module
            driver = importlib.import_module(f"{packageName}.{className}")
        except ModuleNotFoundError:
            # hard stop if driver not
            print(f"{packageName}.{className} not found, refer to install instructions")
            exit(2)

        return driver

    # REQUIRED - a list of devices supported by this class, format is {pkgname.devicename}
    @staticmethod
    def get_supported_devices():
        raise NotImplementedError

    # OPTIONAL - run at the top of each update to do required pre-work
    def prepare(self):
        return True

    # REQUIRED - actual display code, PIL image given
    def display(self, image):
        raise NotImplementedError

    # OPTIONAL - put the display to sleep after each update, if device supports
    def sleep(self):
        return True

    # OPTIONAL - clear the display, if device supports
    def clear(self):
        return True

    # OPTIONAL close out the device, called when the program ends
    def close(self):
        return True
