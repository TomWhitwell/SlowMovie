#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import random
from ffprobe import FFProbe #pip install ffprobe 
from waveshare_epd import epd7in5_V2
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
import subprocess 

viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')
#picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'grabs')
#libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
#if os.path.exists(libdir):
#    sys.path.append(libdir)

epd = epd7in5_V2.EPD()
epd.init()
epd.Clear()
    
frameDelay = 30; 


while 1: 

    #pick a random video file, avoid weird mac system files that start with .
    thisfile = "."
    while thisfile.startswith('.'):
#        thisfile = random.choice(os.listdir("Videos/"))
        thisfile = random.choice(os.listdir(viddir))
        print (thisfile)
#    inputVid = 'Videos/%s'%thisfile
    inputVid = viddir + thisfile
    print (inputVid)
    size = 800, 480

    # Check how many frames are in the movie 
    frameCount = 0 
    metadata=FFProbe(inputVid)
    frameCount =  metadata.streams[0].frames() # only works on simple mp4 files with audio 
    print(frameCount)

    #pick a random frame, assume 24 fps 
    frame = random.randint(0,frameCount)
    msTimecode = "%dms"%(frame*41.666666)
    #open that frame, save as grab.jpg 
    subprocess.call(['ffmpeg', '-ss', msTimecode , '-i', inputVid,  '-vframes', ' 1', '-q:v', '2',  'grab.jpg', '-y', '-nostats', '-loglevel', '0'])
    
#     open and dither grab.jpg 
    pil_im = Image.open("grab.jpg")
    background = Image.new("RGB", size, color=(0,0,0,0))
    pil_im.thumbnail(size)
    old_size = pil_im.size 
    new_size = size 
    background.paste(pil_im, ((new_size[0]-old_size[0])/2,
                          (new_size[1]-old_size[1])/2))
    pil_im = background 
    imageConvert = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

#     Himage = Image.open(fileName %number)
    epd.display(epd.getbuffer(imageConvert))

    time.sleep(frameDelay)



epd.sleep()
    
epd7in5.epdconfig.module_exit()
exit()
