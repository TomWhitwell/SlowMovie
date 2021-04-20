#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import sys
import signal
from waveshare_epd import epd7in5_V2 as epd_driver
from PIL import Image


def exithandler(signum, frame):
    try:
        epd_driver.epdconfig.module_exit()
    finally:
        sys.exit()


signal.signal(signal.SIGTERM, exithandler)
signal.signal(signal.SIGINT, exithandler)

epd = epd_driver.EPD()
epd.init()
epd.Clear()

size = (800, 480)

black = Image.new('1', size, color=0)
white = Image.new('1', size, color=1)

while 1:
    epd.Clear()
    time.sleep(10)
    epd.display(epd.getbuffer(black))
    time.sleep(10)
    epd.display(epd.getbuffer(white))
    time.sleep(10)
