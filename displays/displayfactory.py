import importlib
from . import VirtualDisplayDevice
from . waveshare_display import WaveshareDisplay

def list_supported_displays():
    result = []

    # get a list of display classes extending VirtualDisplayDevice
    displayClasses = [(cls.__module__, cls.__name__) for cls in VirtualDisplayDevice.__subclasses__()]

    for modName, className in displayClasses:
        # load the module the class belongs to
        mod = importlib.import_module(f"{modName}")
        # get the class
        classObj = getattr(mod, className)
        # append supported devices of this class
        result.append(classObj.get_supported_devices())

    return sorted(result)

def load_display_driver(displayName):
    deviceType = displayName.split('.')

    if(deviceType[0] == 'waveshare'):
        return WaveshareDisplay(deviceType[1])
