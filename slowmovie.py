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
import fnmatch
import argparse
import signal

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

fileTypes = [".mp4", ".mkv"]
HOME_DIR = os.path.dirname(os.path.realpath(__file__))
NOW_PLAYING = os.path.join(HOME_DIR, 'nowPlaying')

# function to handle when the is killed and exit gracefully
def signal_handler(signum, frame):
    print('Exiting Program')

    # must init to get gpio pins setup correctly and then exit properly
    epd_driver.epdconfig.module_init()
    epd_driver.epdconfig.module_exit()
    exit(0)

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

def get_video_info(file):
    # get info from ffprobe
    probeInfo = ffmpeg.probe(file)

    frameCount = int(probeInfo['streams'][0]['nb_frames'])

    # calculate the fps
    frameRateStr = probeInfo['streams'][0]['r_frame_rate'].split('/')
    frameRate = float(frameRateStr[0])/float(frameRateStr[1])

    return {'frame_count': frameCount, 'fps': frameRate,
            'runtime': frameCount/frameRate}


def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value


def check_dir(value):
    if(not os.path.exists(value) and not os.path.isdir(value)):
        raise argparse.ArgumentTypeError("%s is not a directory" % value)
    return value


parser = argparse.ArgumentParser(description='SlowMovie Settings')
parser.add_argument('-r', '--random', action='store_true',
    help="Random mode: chooses a random frame every refresh")
parser.add_argument('-f', '--file', type=check_mp4,
    help="Add a filename to start playing a specific film. Otherwise will pick a random file, and will move to another film randomly afterwards.")
parser.add_argument('-D', '--dir', type=check_dir,
    help='Set the directory that contains the video files. Default is ./Videos/')
parser.add_argument('-d', '--delay',  default=120,
    help="Delay between screen updates, in seconds")
parser.add_argument('-i', '--inc',  default=4,
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start',
    help="Start at a specific frame")
args = parser.parse_args()

# add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# set paths to log and video directories
viddir = os.path.join(HOME_DIR, 'Videos/')
logdir = os.path.join(HOME_DIR, 'logs/')

if(args.dir):
    viddir = args.dir

print("Video directory = %s" % viddir)

frameDelay = float(args.delay)
print("Frame Delay = %f" %frameDelay )

increment = float(args.inc)
print("Increment = %f" %increment )

if args.random:
    print("In random mode")
else:
    print ("In play-through mode")

if args.file:
    print('Try to start playing %s' %args.file)
else:
    print ("Continue playing existing file")

# get all mp4 files in video directory
movieList = sorted(fnmatch.filter(os.listdir(viddir), '*.mp4'))
print (movieList)

# log files store the current progress for all the videos available
for file in movieList:
    try:
        log = open(logdir +'%s<progress'%file)
        log.close()
    except:
        log = open(logdir + '%s<progress' %file, "w")
        log.write("0")
        log.close()

currentVideo = None
if args.file:
    if args.file in movieList:
        currentVideo = args.file
    else:
        print('Error loading given file %s' % args.file)
else:
    # the nowPlaying file stores the current video file
    # if it exists and has a valid video, switch to that
    try:
        f = open(NOW_PLAYING)
        for line in f:
            currentVideo = line.strip()
        f.close()
        print('Found now playing file %s' % currentVideo)
    except Exception as e:
        print(e)
        pass

    if(currentVideo not in viddir):
        currentVideo = None

# if no video found, pick random
if currentVideo is None:
    currentVideo = movieList[0]

try:
    f = open(NOW_PLAYING, 'w')
    f.write(currentVideo)
    f.close()
except:
    pass

print("The current video is %s" %currentVideo)


epd = epd_driver.EPD()

# Initialise and clear the screen
epd.init()
epd.Clear()

currentPosition = 0

# Open the log file and update the current position

log = open(logdir + '%s<progress'%currentVideo)
for line in log:
    currentPosition = float(line)

if args.start:
    print('Start at frame %f' %float(args.start))
    currentPosition = float(args.start)

width = epd.width
height = epd.height

inputVid = viddir + currentVideo

# Check how many frames are in the movie
videoInfo = get_video_info(inputVid)
print("there are %d frames in this video" % videoInfo['frame_count'])

while 1:

    if args.random:
        frame = random.randint(0,videoInfo['frame_count'])
    else:
        frame = currentPosition

    msTimecode = "%dms"%(frame*videoInfo['fps'])

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and put it in memory as frame.bmp
    generate_frame(inputVid, "/dev/shm/frame.bmp", msTimecode)

    # Open grab.jpg in PIL
    pil_im = Image.open("/dev/shm/frame.bmp")

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

    # display the image
    epd.display(epd.getbuffer(pil_im))
    print('Displaying frame %d of %s (%.1f%%)' %(frame,currentVideo,(frame/videoInfo['frame_count'])*100))

    currentPosition = currentPosition + increment
    if currentPosition >= videoInfo['frame_count']:
        currentPosition = 0
        log = open(logdir + '%s<progress'%currentVideo, 'w')
        log.write(str(currentPosition))
        log.close()

        thisVideo = movieList.index(currentVideo)
        if thisVideo < len(movieList)-1:
            currentVideo = movieList[thisVideo+1]
        else:
            currentVideo = movieList[0]

    log = open(logdir + '%s<progress'%currentVideo, 'w')
    log.write(str(currentPosition))
    log.close()


    f = open(NOW_PLAYING, 'w')
    f.write(currentVideo)
    f.close()

    epd.sleep()
    time.sleep(frameDelay)
    epd.init()
