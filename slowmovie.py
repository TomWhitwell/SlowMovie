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
import configargparse
from fractions import Fraction

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
    name, ext = os.path.splitext(value)
    if not ext.lower() in fileTypes:
        raise argparse.ArgumentTypeError("%s is not a supported file type" % value)
    return value

os.chdir(os.path.dirname(os.path.realpath(__file__)))
viddir = "Videos"
logdir = "logs"

parser = configargparse.ArgumentParser(default_config_files=["slowmovie.conf"])
parser.add_argument("-r", "--random", action = "store_true", help = "Display random frames")
parser.add_argument("-f", "--file", type = check_mp4, help = "Specify an MP4 file to play")
parser.add_argument("-d", "--delay", default = timeInterval, type = int, help = "Time between updates, in seconds")
parser.add_argument("-i", "--increment", default = frameIncrement, type = int, help = "Number of frames to advance on update")
parser.add_argument("-s", "--start", type = int, help = "Start at a specific frame")
parser.add_argument("-c", "--contrast", default=contrast, type=float, help = "Adjust image contrast (default: 1.0)")
args = parser.parse_args()

if not os.path.isdir(logdir):
    os.mkdir(logdir)
if not os.path.isdir(viddir):
    os.mkdir(viddir)

currentVideo = args.file

if not currentVideo and os.path.isfile("nowPlaying"):
    # the nowPlaying file stores the current video file
    # if it exists and has a valid video, use that
    with open("nowPlaying") as file:
        lastVideo = file.readline().strip()
        if os.path.isfile(lastVideo):
            currentVideo = lastVideo
        else:
            os.remove("nowPlaying")

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

with open("nowPlaying", "w") as file:
    file.write(os.path.abspath(currentVideo))

videoFilename = os.path.basename(currentVideo)
print(f"Playing '{videoFilename}'")

logfile = os.path.join(logdir, videoFilename + ".progress")

epd = epd_driver.EPD()
width = epd.width
height = epd.height

# Check how many frames are in the movie
videoInfo = ffmpeg.probe(currentVideo)
frameCount = int(videoInfo["streams"][0]["nb_frames"])
framerate = videoInfo["streams"][0]["avg_frame_rate"]
framerate = float(Fraction(framerate))
frametime = 1000 / framerate

if not args.random:
    if args.start:
        currentPosition = clamp(args.start, 0, frameCount)
        print("Starting at frame " + str(currentPosition))
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

while 1:
    timeStart = time.perf_counter()
    epd.init()
    if args.random:
        currentPosition = random.randint(0, frameCount)

    msTimecode = "%dms" % (currentPosition * frametime)

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
    #print(f"Diplaying frame {currentPosition} of '{videoFilename}'")
    epd.display(epd.getbuffer(pil_im))

    if not args.random:
        currentPosition += args.increment
        if currentPosition > frameCount:
            currentPosition = 0

        with open(logfile, "w") as log:
            log.write(str(currentPosition))

    epd.sleep()
    timeDiff = time.perf_counter() - timeStart
    #time.sleep(args.delay)
    time.sleep(max(args.delay - timeDiff, 0))
