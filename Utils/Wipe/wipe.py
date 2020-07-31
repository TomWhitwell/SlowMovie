from waveshare_epd import epd7in5_V2
from PIL import Image,ImageDraw,ImageFont
import os, time, sys, random 


epd = epd7in5_V2.EPD()
epd.init()
epd.Clear()
    
size = 800, 480

black = Image.new("1", size, color=0)
white = Image.new("1", size, color=1)

while(1):
    epd.Clear()
    time.sleep(10)
    epd.display(epd.getbuffer(black))
    time.sleep(10)
    epd.display(epd.getbuffer(white))
    time.sleep(10)    

epd.sleep()
    
epd7in5.epdconfig.module_exit()
exit()

