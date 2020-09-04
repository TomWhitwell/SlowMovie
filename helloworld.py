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
from PIL import Image
import ffmpeg

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

def generate_frame(in_filename, out_filename, time, width):
    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter('scale', f"if(gte(a,{width}/{height}),{width},-1)", f"if(gte(a,{width}/{height}),-1,{height})")
        .filter('pad', width, height, -1, -1)
        .output(out_filename, vframes=1)
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

# Ensure this is the correct path to your video folder
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')

epd = epd_driver.EPD()

width = epd.width
height = epd.height

# Initialise and clear the screen
epd.init()
epd.Clear()

while 1:
    # Pick a random .mp4 video in your video directory
    currentVideo = ""
    videos = os.listdir(viddir)
    for file in videos:
        name, ext = os.path.splitext(file)
        if ext != '.mp4':
            videos.remove(file)
    randomVideo = random.randint(0 , len(videos) - 1)
    currentVideo = os.listdir(viddir)[randomVideo]
    inputVid = viddir + currentVideo
    print(inputVid)

    # Check how many frames are in the movie
    videoInfo = ffmpeg.probe(inputVid)
    frameCount = int(videoInfo['streams'][0]['nb_frames'])
    frameRate = videoInfo['streams'][0]['r_frame_rate']

    # Pick a random frame
    frame = random.randint(0, frameCount)

    # Convert that frame to Timecode
    msTimecode = "%dms" % (currentPosition * (1000 / eval(frameRate)))

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as frame.png
    generate_frame(inputVid, '/dev/shm/frame.png', msTimecode, width)

    # Open frame.png in PIL
    pil_im = Image.open('/dev/shm/frame.png')

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode='1', dither=Image.FLOYDSTEINBERG)

    # display the image
    print('Diplaying frame %d of %s' % (frame, currentVideo))
    epd.display(epd.getbuffer(pil_im))

    # Wait for 10 seconds
    time.sleep(10)

# NB We should run sleep() while the display is resting more often, but there's a bug in the driver that's slightly fiddly to fix. Instead of just sleeping, it completely shuts down SPI communication
epd.sleep()
epd_driver.epdconfig.module_exit()