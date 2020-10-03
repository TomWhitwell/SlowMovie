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
import argparse

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

fileTypes = ['.mp4', '.mkv']

def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

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

def check_mp4(value):
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError("%s does not exist" % value)
    name, ext = os.path.splitext(value)
    if not ext.lower() in fileTypes:
        raise argparse.ArgumentTypeError("%s is not a supported file type" % value)
    return value

parser = argparse.ArgumentParser(description='SlowMovie Settings')
parser.add_argument('-r', '--random', action='store_true',
    help="Display random frames")
parser.add_argument('-f', '--file', type=check_mp4,
    help="Specify an MP4 file to play. Otherwise will pick a random file from the videos folder")
parser.add_argument('-d', '--delay', default=120, type=int,
    help="Time between updates, in seconds")
parser.add_argument('-i', '--increment', default=4, type=int,
    help="Number of frames skipped between updates")
parser.add_argument('-s', '--start', type=int,
    help="Start at a specific frame")
parser.add_argument('-c', '--contrast', default=1, type=float,
    help="Adjust image contrast. A value of 1.0 is original contrast")
args = parser.parse_args()

# Ensure this is the correct path to your video folder
scriptdir = os.path.dirname(os.path.realpath(__file__))
viddir = os.path.join(scriptdir, 'Videos')
logdir = os.path.join(scriptdir, 'logs')
nowplayingfile = os.path.join(scriptdir, 'nowPlaying')

if not os.path.isdir(logdir):
    os.mkdir(logdir)
if not os.path.isdir(viddir):
    os.mkdir(viddir)

currentVideo = args.file

if not currentVideo and os.path.isfile(nowplayingfile):
    # the nowPlaying file stores the current video file
    # if it exists and has a valid video, switch to that
    with open(nowplayingfile) as file:
        lastVideo = file.readline()
        if os.path.isfile(lastVideo):
            currentVideo = lastVideo
        else:
            os.remove(nowplayingfile)

if not currentVideo:
    # Iterate through video folder until you find an .mp4 file
    videos = os.listdir(viddir)
    for file in videos:
        name, ext = os.path.splitext(file)
        if ext.lower() in fileTypes:
            currentVideo = os.path.join(viddir, file)
            break

if not currentVideo:
    print("No videos found")
    sys.exit()

print("Update interval: " + str(args.delay))
if not args.random:
    print("Frame increment: " + str(args.increment))

with open(nowplayingfile, 'w') as file:
    file.write(currentVideo)

videoFilename = os.path.basename(currentVideo)
print(f"Playing '{videoFilename}'")

logfile = os.path.join(logdir, videoFilename + '.progress')

epd = epd_driver.EPD()

width = epd.width
height = epd.height

# Check how many frames are in the movie
videoInfo = ffmpeg.probe(currentVideo)
frameCount = int(videoInfo['streams'][0]['nb_frames'])
framerate = videoInfo['streams'][0]['avg_frame_rate']
frametime = 1000 / eval(framerate)

if not args.random:
    if args.start:
        print('Starting at frame ' + str(args.start))
        currentPosition = clamp(args.start, 0, frameCount)
    elif (os.path.isfile(logfile)):
        # Open the log file and update the current position
        with open(logfile) as log:
            try:
                currentPosition = int(log.readline())
                currentPosition = clamp(currentPosition, 0, frameCount)
            except ValueError:
                currentPosition = 0
    else:
        currentPosition = 0

try:
    # Initialise and clear the screen
    epd.init()
    #epd.Clear()

    while 1:
        if args.random:
            currentPosition = random.randint(0, frameCount)

        msTimecode = "%dms" % (currentPosition * frametime)

        # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as frame.bmp
        generate_frame(currentVideo, '/dev/shm/frame.bmp', msTimecode)

        # Open frame.bmp in PIL
        pil_im = Image.open('/dev/shm/frame.bmp')
        if args.contrast != 1:
            enhancer = ImageEnhance.Contrast(pil_im)
            pil_im = enhancer.enhance(args.contrast)

        # Dither the image into a 1 bit bitmap
        pil_im = pil_im.convert(mode='1', dither=Image.FLOYDSTEINBERG)

        # display the image
        print(f"Diplaying frame {currentPosition} of '{videoFilename}'")
        epd.display(epd.getbuffer(pil_im))

        if not args.random:
            currentPosition += args.increment
            if currentPosition > frameCount:
                currentPosition = 0

            with open(logfile, 'w') as log:
                log.write(str(currentPosition))

        epd.sleep()
        time.sleep(args.delay)
        epd.init()
except KeyboardInterrupt:
    pass
finally:
    epd_driver.epdconfig.module_exit()