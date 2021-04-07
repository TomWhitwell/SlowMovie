# representation of a display device, impelenting classes should implement these methods
class VirtualDisplayDevice:
    device = None
    name = "virtualdevice"
    width = 0
    height = 0

    def __init__(self, deviceName):
        self.name = deviceName

    def __str__(self):
        return self.name

    # devices supported by this class
    @staticmethod
    def get_supported_devices():
        return []

    # run at the top of each update
    def prepare(self):
        return True

    # actual display, PIL image given
    def display(self, image, **kwargs):
        return True

    # put the display to sleep
    def sleep(self):
        return True

    # clear the display
    def clear(self):
        return True

    # close out the device when the program ends
    def close(self):
        return True
