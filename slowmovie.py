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
from PIL import Image
import ffmpeg
import argparse

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

fileTypes = [".mp4", ".mkv"]


def generate_frame(in_filename, out_filename, time):
    try:
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
    except ffmpeg.Error as e:
        print('stdout:', e.stdout.decode('utf8'))
        print('stderr:', e.stderr.decode('utf8'))
        raise e

def is_vid(filename):
    return list(filter(filename.endswith, fileTypes)) != []

def check_vid(value):
    if not is_vid(value):
        raise argparse.ArgumentTypeError(f"{value} should be a file with one of the following extensions: {', '.join(fileTypes)}")
    return value

# Ensure this is the correct path to your video folder
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')
logdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs/')


parser = argparse.ArgumentParser(description='SlowMovie Settings')
parser.add_argument('-r', '--random', action='store_true',
    help="Random mode: chooses a random frame every refresh")
parser.add_argument('-f', '--file', type=check_vid,
    help="Add a filename to start playing a specific film. Otherwise will pick a random file, and will move to another film randomly afterwards.")
parser.add_argument('-d', '--delay',  default=120,
    help="Delay between screen updates, in seconds")
parser.add_argument('-i', '--inc',  default=4,
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start',
    help="Start at a specific frame")
args = parser.parse_args()

frameDelay = float(args.delay)
print(f"Frame Delay = {frameDelay}")

increment = float(args.inc)
print(f"Increment = {increment}")

if args.random:
    print("In random mode")
else:
    print ("In play-through mode")

if args.file:
    print(f"Trying to start playing {args.file}")
else:
    print ("Continuing playback from the existing file")

# Scan through video folder until you find a video file
currentVideo = ""
for video in os.listdir(viddir):
    if is_vid(video):
        currentVideo = video
        break

# the nowPlaying file stores the current video file
# if it exists and has a valid video, switch to that
try:
    f = open('nowPlaying')
    for line in f:
        currentVideo = line.strip()
    f.close()
except:
    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close()

videoExists = 0
for file in os.listdir(viddir):
    if file == currentVideo:
        videoExists = 1

if videoExists > 0:
    print(f"The current video is {currentVideo}")
elif videoExists == 0:
    print('error')
    currentVideo = os.listdir(viddir)[0]
    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close()
    print(f"The current video is {currentVideo}")

movieList = []

# log files store the current progress for all the videos available

# Make sure all videos in the /Videos have a corresponding log file
# if they don't create it
for file in os.listdir(viddir):
    if not file.startswith('.'):
        movieList.append(file)
        try:
            log = open(logdir + f"{file}<progress")
            log.close()
        except:
            log = open(logdir + f"{file}<progress", "w")
            log.write("0")
            log.close()

print(f"Movie list: {movieList}")

if args.file:
    if args.file in movieList:
        currentVideo = args.file
    else:
        print (f"{args.file} not found")

print(f"The current video is {currentVideo}")


epd = epd_driver.EPD()

# Initialise and clear the screen
epd.init()
epd.Clear()

currentPosition = 0

# Open the log file and update the current position
log = open(logdir + f"{currentVideo}<progress")
for line in log:
    currentPosition = float(line)

if args.start:
    print(f"Start at frame {float(args.start)}")
    currentPosition = float(args.start)

width = epd.width
height = epd.height

inputVid = viddir + currentVideo

# Check how many frames are in the movie
frameCount = int(ffmpeg.probe(inputVid)['streams'][0]['nb_frames'])
print(f"there are {frameCount} frames in this video")

while 1:

    if args.random:
        frame = random.randint(0,frameCount)
    else:
        frame = currentPosition

    msTimecode = f"{frame*41.666666}ms"

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and put it in memory as frame.bmp
    generate_frame(inputVid, "/dev/shm/frame.bmp", msTimecode)

    # Open grab.jpg in PIL
    pil_im = Image.open("/dev/shm/frame.bmp")

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

    # display the image
    epd.display(epd.getbuffer(pil_im))
    print(f"Displaying frame {int(frame)} of {currentVideo} ({(frame/frameCount)*100}%)")

    currentPosition = currentPosition + increment
    if currentPosition >= frameCount:
        currentPosition = 0
        log = open(logdir + f"{currentVideo}s<progress", 'w')
        log.write(str(currentPosition))
        log.close()

        thisVideo = movieList.index(currentVideo)
        if thisVideo < len(movieList)-1:
            currentVideo = movieList[thisVideo+1]
        else:
            currentVideo = movieList[0]

    log = open(logdir + f"{currentVideo}<progress", 'w')
    log.write(str(currentPosition))
    log.close()


    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close()


    epd.sleep()
    time.sleep(frameDelay)
    epd.init()


epd.sleep()

epd7in5.epdconfig.module_exit()
exit()
