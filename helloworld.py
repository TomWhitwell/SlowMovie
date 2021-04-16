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

import os
import time
import sys
import random
import signal
import ffmpeg
from PIL import Image
from fractions import Fraction

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver


def exithandler(signum, frame):
    try:
        epd_driver.epdconfig.module_exit()
    finally:
        sys.exit()


signal.signal(signal.SIGTERM, exithandler)
signal.signal(signal.SIGINT, exithandler)


def generate_frame(in_filename, out_filename, time):
    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter("scale", "iw*sar", "ih")
        .filter("scale", width, height, force_original_aspect_ratio=1)
        .filter("pad", width, height, -1, -1)
        .output(out_filename, vframes=1)
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )


def supported_filetype(file):
    _, ext = os.path.splitext(file)
    return ext.lower() == ".mp4"


# Ensure this is the correct path to your video folder
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Videos")
if not os.path.isdir(viddir):
    os.mkdir(viddir)

epd = epd_driver.EPD()
width = epd.width
height = epd.height

while 1:
    epd.init()

    # Pick a random .mp4 video in your video directory
    videos = list(filter(supported_filetype, os.listdir(viddir)))
    if not videos:
        print("No videos found")
        sys.exit()
    currentVideo = os.path.join(viddir, random.choice(videos))

    # Get framerate and frame count
    videoInfo = ffmpeg.probe(currentVideo)
    frameCount = int(videoInfo["streams"][0]["nb_frames"])
    framerate = videoInfo["streams"][0]["avg_frame_rate"]
    framerate = float(Fraction(framerate))
    frametime = 1000 / framerate

    # Pick a random frame
    frame = random.randint(0, frameCount)

    # Convert that frame to Timecode
    msTimecode = "%dms" % (frame * frametime)

    # Use ffmpeg to extract a frame from the movie, letterbox/pillarbox, and save it
    generate_frame(currentVideo, "/dev/shm/frame.bmp", msTimecode)

    # Open image in PIL
    pil_im = Image.open("/dev/shm/frame.bmp")

    # display the image
    print(f"Displaying frame {frame} of '{os.path.basename(currentVideo)}'")
    epd.display(epd.getbuffer(pil_im))

    # Wait for 10 seconds
    epd.sleep()
    time.sleep(10)
