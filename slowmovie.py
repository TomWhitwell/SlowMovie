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

import os, time, sys, random, signal
from PIL import Image, ImageEnhance
import ffmpeg
from fractions import Fraction

try:
    import configargparse
except ImportError:
    import argparse

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

# Defaults
frameIncrement = 4
timeInterval = 120
contrast = 1.0

fileTypes = [".mp4", ".mkv"]

def exithandler(signum, frame):
    epd_driver.epdconfig.module_exit()
    sys.exit()

signal.signal(signal.SIGTERM, exithandler)
signal.signal(signal.SIGINT, exithandler)

def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

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

def check_mp4(value):
    if not os.path.isfile(value):
        raise argparse.ArgumentTypeError("%s does not exist" % value)
    if not supported_filetype(value):
        raise argparse.ArgumentTypeError("%s is not a supported file type" % value)
    return value

def supported_filetype(file):
    _, ext = os.path.splitext(file)
    return ext.lower() in fileTypes

def video_info(file):
    videoInfo = ffmpeg.probe(file)
    frameCount = int(videoInfo["streams"][0]["nb_frames"])
    framerate = videoInfo["streams"][0]["avg_frame_rate"]
    framerate = float(Fraction(framerate))
    frametime = 1000 / framerate
    return frameCount, framerate, frametime

os.chdir(os.path.dirname(os.path.realpath(__file__)))
viddir = "Videos"
logdir = "logs"

if "configargparse" in sys.modules:
    parser = configargparse.ArgumentParser(default_config_files=["slowmovie.conf"])
else:
    parser = argparse.ArgumentParser()
parser.add_argument("-r", "--random", action = "store_true", help = "Display random frames")
parser.add_argument("-f", "--file", type = check_mp4, help = "Specify an MP4 file to play")
parser.add_argument("-d", "--delay", default = timeInterval, type = int, help = "Time between updates, in seconds")
parser.add_argument("-i", "--increment", default = frameIncrement, type = int, help = "Number of frames to advance on update")
parser.add_argument("-s", "--start", type = int, help = "Start at a specific frame")
parser.add_argument("-c", "--contrast", default=contrast, type=float, help = "Adjust image contrast (default: 1.0)")
parser.add_argument("-a", "--adjust-delay", action = "store_true", help = "Reduce delay by the amount of time taken to display a frame.")
parser.add_argument("-l", "--loop", action = "store_true", help = "Loop single video.")
args = parser.parse_args()

if not os.path.isdir(logdir):
    os.mkdir(logdir)
if not os.path.isdir(viddir):
    os.mkdir(viddir)

# First we try the file argument...
currentVideo = args.file

# ...then the last played file...
if not currentVideo and os.path.isfile("nowPlaying"):
    with open("nowPlaying") as file:
        lastVideo = file.readline().strip()
        if os.path.isfile(lastVideo):
            currentVideo = lastVideo
        else:
            os.remove("nowPlaying")

# ...then we look in the videos folder.
if not currentVideo:
    videos = os.listdir(viddir)
    for file in videos:
        if supported_filetype(file):
            currentVideo = os.path.join(viddir, file)
            break

# If none of the above worked, exit.
if not currentVideo:
    print("No videos found")
    sys.exit()

print("Update interval: " + str(args.delay))
if not args.random:
    print("Frame increment: " + str(args.increment))

with open("nowPlaying", "w") as file:
    file.write(os.path.abspath(currentVideo))

videoFilename = os.path.basename(currentVideo)

if not args.loop:
    viddir = os.path.dirname(currentVideo)
    videos = list(filter(supported_filetype, os.listdir(viddir)))
    fileIndex = videos.index(videoFilename)

logfile = os.path.join(logdir, videoFilename + ".progress")

epd = epd_driver.EPD()
width = epd.width
height = epd.height

frameCount, framerate, frametime = video_info(currentVideo)

if not args.random:
    if args.start:
        currentFrame = clamp(args.start, 0, frameCount)
        print("Starting at frame " + str(currentFrame))
    elif (os.path.isfile(logfile)):
        # Read current frame from logfile
        with open(logfile) as log:
            try:
                currentFrame = int(log.readline())
                currentFrame = clamp(currentFrame, 0, frameCount)
            except ValueError:
                currentFrame = 0
    else:
        currentFrame = 0

lastVideo = None

while 1:
    if lastVideo != currentVideo:
        print(f"Playing '{videoFilename}'")
        lastVideo = currentVideo

    timeStart = time.perf_counter()
    epd.init()

    if args.random:
        currentFrame = random.randint(0, frameCount)

    msTimecode = "%dms" % (currentFrame * frametime)

    # Use ffmpeg to extract a frame from the movie, letterbox/pillarbox it and save it as frame.bmp
    generate_frame(currentVideo, "/dev/shm/frame.bmp", msTimecode)

    # Open frame.bmp in PIL
    pil_im = Image.open("/dev/shm/frame.bmp")

    if args.contrast != 1:
        enhancer = ImageEnhance.Contrast(pil_im)
        pil_im = enhancer.enhance(args.contrast)

    # Dither the image into a 1 bit bitmap
    #pil_im = pil_im.convert(mode = "1", dither = Image.FLOYDSTEINBERG)

    # display the image
    #print(f"Displaying frame {currentFrame} of '{videoFilename}'")
    epd.display(epd.getbuffer(pil_im))

    if not args.random:
        currentFrame += args.increment
        if currentFrame > frameCount:
            # end of video
            if not args.loop:
                # go to next video in folder
                fileIndex += 1

                if fileIndex >= len(videos):
                    # last video in folder; go to first
                    fileIndex = 0

                videoFilename = videos[fileIndex]
                currentVideo = os.path.join(viddir, videoFilename)

                with open("nowPlaying", "w") as file:
                    file.write(os.path.abspath(currentVideo))

                logfile = os.path.join(logdir, videoFilename + ".progress")
                frameCount, framerate, frametime = video_info(currentVideo)

            currentFrame = 0

        with open(logfile, "w") as log:
            log.write(str(currentFrame))

    epd.sleep()
    timeDiff = time.perf_counter() - timeStart
    if args.adjust_delay:
        time.sleep(max(args.delay - timeDiff, 0))
    else:
        time.sleep(args.delay)
