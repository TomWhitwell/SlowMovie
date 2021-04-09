import importlib
from . import VirtualDisplayDevice
from . waveshare_display import WaveshareDisplay  # noqa: F401
from . mock_display import MockDisplay  # noqa: F401


def list_supported_displays(as_dict=False):
    result = []

    # get a list of display classes extending VirtualDisplayDevice
    displayClasses = [(cls.__module__, cls.__name__) for cls in VirtualDisplayDevice.__subclasses__()]

    for modName, className in displayClasses:
        # load the module the class belongs to
        mod = importlib.import_module(modName)
        # get the class
        classObj = getattr(mod, className)

        if(as_dict):
            result.append({'package': modName, 'class': className, 'devices': classObj.get_supported_devices()})
        else:
            # add supported devices of this class
            result = sorted(result + classObj.get_supported_devices())

    return result


def load_display_driver(displayName):
    result = None

    # get a dict of all valid display device classes
    displayClasses = list_supported_displays(True)
    foundClass = list(filter(lambda d: displayName in d['devices'], displayClasses))

    if(len(foundClass) == 1):
        # split on the pkg.classname
        deviceType = displayName.split('.')

        # create the class and initialize
        mod = importlib.import_module(foundClass[0]['package'])
        classObj = getattr(mod, foundClass[0]['class'])

        result = classObj(deviceType[1])
    else:
        # we have a problem
        print(f"Suitable display device cannot be loaded for {displayName}")
        exit(1)

    return result
