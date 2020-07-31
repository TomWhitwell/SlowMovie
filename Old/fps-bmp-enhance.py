import random 
import numpy as np
from PIL import Image, ImageEnhance
import os, time, sys, random 
from ffprobe import FFProbe #pip install ffprobe 
import traceback
import subprocess 
from waveshare_epd import epd7in5_V2

mode = random 
inputVid = 'Videos/Psycho.mp4'

size = 800, 480

epd = epd7in5_V2.EPD()
epd.init()
epd.Clear()
while 1:
    # Check how many frames are in the movie 
    frameCount = 0 
    metadata=FFProbe(inputVid)
    frameCount =  metadata.streams[0].frames() # only works on simple mp4 files with audio 


    frame = random.randint(0,frameCount)

    msTimecode = "%dms"%(frame*41.666666)
    #open that frame, save as grab.jpg 
    subprocess.call(['ffmpeg', '-ss', msTimecode , '-i', inputVid,  '-vframes', ' 1', '-q:v', '2',  'grab.jpg', '-y', '-nostats', '-loglevel', '0'])

    #     open and dither grab.jpg 
    pil_im = Image.open("grab.jpg")
    enhancer = ImageEnhance.Contrast(pil_im)
    enhanced = enhancer.enhance(1.2)
    # pil_im = pil_im.ImageEnhance.Contrast(2.0)

    background = Image.new("RGB", size, color=(0,0,0,0))
    pil_im.thumbnail(size)
    old_size = pil_im.size 
    new_size = size 
    background.paste(pil_im, ((new_size[0]-old_size[0])/2,
                          (new_size[1]-old_size[1])/2))
    pil_im = background 
    # imageConvert = pil_im
    imageConvert = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)
    epd.display(epd.getbuffer(imageConvert))
    time.sleep(10)
    background2 = Image.new("RGB", size, color=(0,0,0,0))
    enhanced.thumbnail(size)
    old_size = enhanced.size 
    new_size = size 
    background2.paste(enhanced, ((new_size[0]-old_size[0])/2,
                          (new_size[1]-old_size[1])/2))
    enhanced = background2 
    enhanced = enhanced.convert(mode='1',dither=Image.FLOYDSTEINBERG)
    epd.display(epd.getbuffer(enhanced))
    time.sleep(10)

