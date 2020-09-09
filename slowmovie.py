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
import argparse

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

# Ensure this is the correct path to your video folder
scriptdir = os.path.dirname(os.path.realpath(__file__))
viddir = os.path.join(scriptdir, 'Videos')
logdir = os.path.join(scriptdir, 'logs')
nowplayingfile = os.path.join(scriptdir, 'nowPlaying')

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
    if not ext == '.mp4':
        raise argparse.ArgumentTypeError("%s should be an MP4 file" % value)
    return value

parser = argparse.ArgumentParser(description='SlowMovie Settings')
parser.add_argument('-r', '--random', action='store_true',
    help="Random mode: chooses a random frame every refresh")
parser.add_argument('-f', '--file', type=check_mp4,
    help="Specify an MP4 file to play. Otherwise will pick a random file from the videos folder")
parser.add_argument('-d', '--delay',  default=120, type=int,
    help="Time between screen updates, in seconds")
parser.add_argument('-i', '--increment',  default=4, type=int,
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', type=int,
    help="Start at a specific frame")
args = parser.parse_args()

print("Frame delay: %d" % args.delay )
print("Increment: %d" % args.increment )

if args.random:
    print("Random mode")

if args.file:
    currentVideo = args.file
else:
    currentVideo = ""

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
        if ext.lower() == '.mp4':
            currentVideo = os.path.join(viddir, file)
            break

if not currentVideo:
    print("No videos found")
    sys.exit()

with open(nowplayingfile, 'w') as file:
    file.write(currentVideo)

videoFilename = os.path.basename(currentVideo)
print("Playing " + videoFilename)

# log files store the current progress for all the videos available
if not os.path.isdir(logdir):
    os.mkdir(logdir)

logfile = os.path.join(logdir, videoFilename + '.progress')

try:
    log = open(logfile)
    log.close()
except:
    log = open(logfile, "w")
    log.write("0")
    log.close()

epd = epd_driver.EPD()

width = epd.width
height = epd.height

currentPosition = 0

# Open the log file and update the current position
with open(logfile) as log:
    currentPosition = int(log.readline())

if args.start:
    print('Start at frame %d' % args.start)
    currentPosition = args.start

inputVid = currentVideo

# Check how many frames are in the movie
videoInfo = ffmpeg.probe(currentVideo)
frameCount = int(videoInfo['streams'][0]['nb_frames'])
framerate = videoInfo['streams'][0]['avg_frame_rate']
frametime = 1000 / eval(framerate)
print("There are %d frames in this video" % frameCount)

try:
    # Initialise and clear the screen
    epd.init()
    #epd.Clear()

    while 1:
        if args.random:
            currentPosition = random.randint(0, frameCount)

        msTimecode = "%dms" % (currentPosition * frametime)

        # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as frame.png
        generate_frame(currentVideo, '/dev/shm/frame.bmp', msTimecode)

        # Open frame.png in PIL
        pil_im = Image.open('/dev/shm/frame.bmp')

        # Dither the image into a 1 bit bitmap
        pil_im = pil_im.convert(mode='1', dither=Image.FLOYDSTEINBERG)

        # display the image
        print('Diplaying frame %d of %s' % (currentPosition, videoFilename))
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
    print('Exiting...')
finally:
    epd.sleep()
    epd_driver.epdconfig.module_exit()
