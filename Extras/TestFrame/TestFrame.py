#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PIL import Image
from waveshare_epd import epd7in5_V2 as epd_driver

epd = epd_driver.EPD()
epd.init()
epd.Clear()
img = Image.open('test-frame.BMP')
img = img.convert(mode='1', dither=Image.FLOYDSTEINBERG)
epd.display(epd.getbuffer(img))
epd.sleep()
