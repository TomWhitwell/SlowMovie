from . import VirtualDisplayDevice


# this is a reference implementation of a display extending VirtualDisplayDevice
# it does not physically write to anything but can be used as a mock testing device
class MockDisplay(VirtualDisplayDevice):
    pkg_name = 'slowmovie'

    def __init__(self, deviceName):
        super(MockDisplay, self).__init__(deviceName)

        # this is normally where you'd load actual device class but nothing to load here

        # set the width and height - doesn't matter since we won't write anything
        self.width = 100
        self.height = 100

    @staticmethod
    def get_supported_devices():
        # only one display supported, the test display
        return [f"{MockDisplay.pkg_name}.mock"]

    def prepare(self):
        print(f"preparing {self.__str__()}")

    def display(self, image):
        print(f"writing image to {self.__str__()}")

    def sleep(self):
        print(f"{self.__str__()} is sleeping")

    def clear(self):
        print(f"clearing {self.__str__()}")

    def close(self):
        print(f"closing {self.__str__()}")
