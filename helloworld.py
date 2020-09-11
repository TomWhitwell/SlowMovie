#!/usr/bin/python3
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
from PIL import Image, ImageEnhance
import ffmpeg

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

def generate_frame(in_filename, out_filename, time):
    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter('scale', 'iw*sar', 'ih')
        #.filter('setsar', '1')
        .filter('scale', f"if(gte(a,{width}/{height}),{width},-1)", f"if(gte(a,{width}/{height}),-1,{height})")
        .filter('pad', width, height, -1, -1)
        .output(out_filename, vframes=1)
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

# Ensure this is the correct path to your video folder
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos')
if not os.path.isdir(viddir):
    os.mkdir(viddir)
    
fileTypes = ['.mp4', '.mkv']

epd = epd_driver.EPD()

width = epd.width
height = epd.height

try:
    # Initialise and clear the screen
    epd.init()
    #epd.Clear()

    while 1:
        # Pick a random .mp4 video in your video directory
        videos = os.listdir(viddir)
        for file in videos:
            name, ext = os.path.splitext(file)
            if not ext.lower() in fileTypes:
                videos.remove(file)

        if not videos:
            print('No videos found')
            sys.exit()

        randomVideo = random.randint(0 , len(videos) - 1)
        currentVideo = videos[randomVideo]
        inputVid = os.path.join(viddir, currentVideo)
        print(inputVid)

        # Check how many frames are in the movie
        videoInfo = ffmpeg.probe(inputVid)
        frameCount = int(videoInfo['streams'][0]['nb_frames'])
        frameRate = videoInfo['streams'][0]['avg_frame_rate']

        # Pick a random frame
        frame = random.randint(0, frameCount)

        # Convert that frame to Timecode
        msTimecode = "%dms" % (frame * (1000 / eval(frameRate)))

        # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as frame.bmp
        generate_frame(inputVid, '/dev/shm/frame.bmp', msTimecode)

        # Open frame.bmp in PIL
        pil_im = Image.open('/dev/shm/frame.bmp')
        enhancer = ImageEnhance.Contrast(pil_im)
        pil_im = enhancer.enhance(2)

        # Dither the image into a 1 bit bitmap (Just zeros and ones)
        pil_im = pil_im.convert(mode='1', dither=Image.FLOYDSTEINBERG)

        # display the image
        print('Diplaying frame %d of %s' % (frame, currentVideo))
        epd.display(epd.getbuffer(pil_im))

        # Wait for 10 seconds
        epd.sleep()
        time.sleep(10)
        epd.init()
except KeyboardInterrupt:
    pass
finally:
    epd_driver.epdconfig.module_exit()
