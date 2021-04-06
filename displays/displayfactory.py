from . waveshare_display import WaveshareDisplay

def list_supported_displays():
    result = WaveshareDisplay.get_supported_devices()

    return result

def load_display_driver(displayName):
    deviceType = displayName.split('.')

    if(deviceType[0] == 'waveshare'):
        return WaveshareDisplay(deviceType[1])
