#!/usr/bin/python
# -*- coding:utf-8 -*-

# *************************
# ** Before running this **
# ** code ensure you've  **
# ** turned on SPI on    **
# ** your Raspberry Pi   **
# ** & installed the     **
# ** Waveshare library   **
# *************************

import os, time, sys, random 
from ffprobe import FFProbe #pip install ffprobe 
from PIL import Image,ImageDraw,ImageFont
import subprocess

# Ensure this is the correct import for your particular screen 
from waveshare_epd import epd7in5_V2

# Ensure this is the correct path to your video folder 
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')

# Ensure this is the correct driver for your particular screen 
epd = epd7in5_V2.EPD()


# Initialise and clear the screen 
epd.init()
epd.Clear()    

# Find the first video in your video directory 
currentVideo = os.listdir(viddir)[0]
inputVid = viddir + currentVideo

# Ensure this matches your particular screen 
size = 800, 480
    
# Check how many frames are in the movie 
frameCount = 0 
metadata=FFProbe(inputVid)
frameCount =  metadata.streams[0].frames() # only works on simple mp4 files with audio 
print("there are %d frames in this video" %frameCount)

while 1: 
    # Pick a random frame 
    frame = random.randint(0,frameCount)

    # Convert that frame to Timecode 
    msTimecode = "%dms"%(frame*41.666666)
    
    # Use ffmpeg running locally to extract a frame from the movie and save it as grab.jpg 
    # There are ffmpeg wrappers for Python that would probably make this neater 
    subprocess.call(['ffmpeg', '-ss', msTimecode , '-i', inputVid,  '-vframes', ' 1', '-q:v', '2',  'grab.jpg', '-y', '-nostats', '-loglevel', '0'])
    
    # Open grab.jpg in PIL  
    pil_im = Image.open("grab.jpg")
    
    # Create a blank black frame the size of the screen 
    background = Image.new("RGB", size, color=(0,0,0,0))

    #resize the frame to fit 
    pil_im.thumbnail(size)

    # paste the resized image into the blank background 
    old_size = pil_im.size 
    new_size = size 
    background.paste(pil_im, ((new_size[0]-old_size[0])/2,
                          (new_size[1]-old_size[1])/2))

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = background 
    imageConvert = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

    # display the image 
    epd.display(epd.getbuffer(imageConvert))
    print('Diplaying frame %d of %s' %(frame,currentVideo))
    
    # Wait for 30 seconds 
    time.sleep(30)
    
# NB We should really run sleep() more often, but there's a bug in the demo code that's slightly fiddly to fix, so instead of just sleeping, it completely shuts down SPI communication 
epd.sleep()

epd7in5.epdconfig.module_exit()
exit()
