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
from waveshare_epd import epd7in5_V2

def generate_frame(in_filename, out_filename, time, width, height):    
    (
        ffmpeg
        .input(in_filename, ss=time)
        .filter('scale', width, height, force_original_aspect_ratio=1)
        .filter('pad', width, height, -1, -1)
        .output(out_filename, vframes=1)              
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value

# Ensure this is the correct path to your video folder 
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')
logdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs/')


parser = argparse.ArgumentParser(description='SlowMovie Settings')
parser.add_argument('-r', '--random', action='store_true', 
    help="Random mode: chooses a random frame every refresh")
parser.add_argument('-f', '--file', type=check_mp4,
    help="Add a filename to start playing a specific film. Otherwise will pick a random file, and will move to another film randomly afterwards.")
parser.add_argument('-d', '--delay',  default=120, 
    help="Delay between screen updates, in seconds")
parser.add_argument('-i', '--inc',  default=4, 
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start',  
    help="Start at a specific frame")
args = parser.parse_args()

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

# Scan through video folder until you find an .mp4 file 
currentVideo = ""
videoTry = 0 
while not (currentVideo.endswith('.mp4')):
    currentVideo = os.listdir(viddir)[videoTry]
    videoTry = videoTry + 1 

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
    print("The current video is %s" %currentVideo)
elif videoExists == 0: 
    print('error')
    currentVideo = os.listdir(viddir)[0]
    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close() 
    print("The current video is %s" %currentVideo)

movieList = []

# log files store the current progress for all the videos available 

for file in os.listdir(viddir):
    if not file.startswith('.'):
        movieList.append(file)
        try: 
            log = open(logdir +'%s<progress'%file)
            log.close()
        except: 
            log = open(logdir + '%s<progress' %file, "w")
            log.write("0")
            log.close()

print (movieList)

if args.file: 
    if args.file in movieList:
        currentVideo = args.file
    else: 
        print ('%s not found' %args.file)

print("The current video is %s" %currentVideo)

# Ensure this is the correct driver for your particular screen 
epd = epd7in5_V2.EPD()

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

# Ensure this matches your particular screen 
width = 800 
height = 480 

inputVid = viddir + currentVideo

# Check how many frames are in the movie 
frameCount = int(ffmpeg.probe(inputVid)['streams'][0]['nb_frames'])
print("there are %d frames in this video" %frameCount)

while 1: 

    if args.random:
        frame = random.randint(0,frameCount)
    else: 
        frame = currentPosition

    msTimecode = "%dms"%(frame*41.666666)
        
    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as grab.jpg 
    generate_frame(inputVid, 'grab.jpg', msTimecode, width, height)
    
    # Open grab.jpg in PIL  
    pil_im = Image.open("grab.jpg")
    
    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

    # display the image 
    epd.display(epd.getbuffer(pil_im))
    print('Diplaying frame %d of %s' %(frame,currentVideo))
    
    currentPosition = currentPosition + increment 
    if currentPosition >= frameCount:
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


    f = open('nowPlaying', 'w')
    f.write(currentVideo)
    f.close() 
    

#     epd.sleep()
    time.sleep(frameDelay)
    epd.init()




epd.sleep()
    
epd7in5.epdconfig.module_exit()
exit()
