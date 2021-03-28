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
# from pprint import pprint

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


parser = argparse.ArgumentParser(description='Show a movie one frame at a time on an e-paper screen')
parser.add_argument('-f', '--file',
    type=check_vid,
    help="filename of video to start playing; otherwise play the first file and then move to another file randomly afterwards")
parser.add_argument('-d', '--delay',
    type=float,
    default=120,
    help="delay in seconds between screen updates (default: %(default)s)")
parser.add_argument('-i', '--inc',
    type=float,
    default=4,
    help="advance INC frames each refresh (default: %(default)s)")
parser.add_argument('-s', '--start',
    type=float,
    help="start playing at a specific frame")
parser.add_argument('-r', '--random',
    action='store_true',
    help="choose a random frame every refresh")
args = parser.parse_args()

print(f"Frame Delay = {args.delay}")

print(f"args.inc = {args.inc}")

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

if currentVideo in os.listdir(viddir):
    print(f"The current video is {currentVideo}")
else:
    print('Current video not found, playing first video available')
    currentVideo = os.listdir(viddir)[0]
    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close()
    print(f"The current video is {currentVideo}")

# log files store the current progress for all the videos available

# Make sure all videos in the /Videos have a corresponding log file
# if they don't create it
movieList = []
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

print(f"{movieList = })

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
    print(f"Start at frame {args.start}")
    currentPosition = args.start

width = epd.width
height = epd.height

# Check how many frames are in the movie
inputVid = viddir + currentVideo
probe = ffmpeg.probe(inputVid)
# print("probe:")
# pprint(probe)
stream = probe['streams'][0]
try:
    # get frames for .mp4s
    frameCount = int(stream['nb_frames'])
except KeyError:
    # get frames for .mkvs (and maybe other?)
    # https://github.com/fepegar/utils/commit/f52ab5152eaa5b8ceadefee172e985aaab3a9947#diff-521f42b0315f6bf8900be8407965552a8f6b32d9a22c09178c55be62b1bef4a2R23-R39
    r_fps = stream['r_frame_rate']
    try:
        num, denom = r_fps.split('/')
    except ValueError:
        # if r_fps isn't a fraction (does this happen?)
        num = r_fps
        denom = 1
    fps = float(num) / float(denom)
    duration = float(probe['format']['duration'])
    frameCount = int(duration * fps)

print(f"there are {frameCount} frames in this video")

while True:

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
    print(f"Displaying frame {int(frame)} of {currentVideo} ({(frame/frameCount)*100:.1f}%)")
    epd.display(epd.getbuffer(pil_im))

    # increment the position
    currentPosition = currentPosition + args.inc

    if currentPosition >= frameCount:
        currentPosition = 0
        log = open(logdir + f"{currentVideo}<progress", 'w')
        log.write(str(currentPosition))
        log.close()

        # move on to the next video
        if currentVideo == movieList[-1]:
            currentVideo = movieList[0]
        else:
            currentVideo = movieList[movieList.index(currentVideo)+1]

    log = open(logdir + f"{currentVideo}<progress", 'w')
    log.write(str(currentPosition))
    log.close()

    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close()

    epd.sleep()
    time.sleep(args.delay)
    epd.init()

epd.sleep()

epd7in5.epdconfig.module_exit()
exit()
