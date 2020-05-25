#!/usr/bin/python
# -*- coding:utf-8 -*-
import os, time, sys, random 
from ffprobe import FFProbe #pip install ffprobe 
from waveshare_epd import epd7in5_V2
from PIL import Image,ImageDraw,ImageFont
import traceback
import subprocess 

viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Videos/')
logdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs/')


epd = epd7in5_V2.EPD()
epd.init()
epd.Clear()
    

# Options: python keepyp.py mode movie frameDelay increment 
# mode = play or random 
# movie = specify full filename 
# frameDelay in seconds 
# increment in frames 


try: 
    frameDelay = float(sys.argv[3])
except: 
    frameDelay = 10

print("Frame Delay = %f" %frameDelay )

try:
    increment = float(sys.argv[4])
except:
    increment = 1
print("Increment = %f" %increment )



try:
    if sys.argv[1].strip() == 'play' or sys.argv[1].strip() == 'random':
        mode = sys.argv[1]
    else:
        mode = 'play'    
except:
    mode = 'play'

print("Mode=%s" %mode)

currentVideo = os.listdir(viddir)[0]

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

try:
    argVideo = sys.argv[2].strip()
    if argVideo in movieList:
        currentVideo = argVideo
        print('****loading %s ****' %currentVideo)
except:
    argVideo = currentVideo

print("The current video is %s" %currentVideo)


currentPosition = 0

log = open(logdir + '%s<progress'%currentVideo)
for line in log:
    print('found this line: %s' %line)
    currentPosition = float(line)


while 1: 

    size = 800, 480
    inputVid = viddir + currentVideo

    # Check how many frames are in the movie 
    frameCount = 0 
    metadata=FFProbe(inputVid)
    frameCount =  metadata.streams[0].frames() # only works on simple mp4 files with audio 


    if mode == 'random':
        frame = random.randint(0,frameCount)
    else: 
        frame = currentPosition


    msTimecode = "%dms"%(frame*41.666666)
    #open that frame, save as grab.jpg 
    subprocess.call(['ffmpeg', '-ss', msTimecode , '-i', inputVid,  '-vframes', ' 1', '-q:v', '2',  'grab.jpg', '-y', '-nostats', '-loglevel', '0'])
    
#     open and dither grab.jpg 
    pil_im = Image.open("grab.jpg")
    background = Image.new("RGB", size, color=(0,0,0,0))
    pil_im.thumbnail(size)
    old_size = pil_im.size 
    new_size = size 
    background.paste(pil_im, ((new_size[0]-old_size[0])/2,
                          (new_size[1]-old_size[1])/2))
    pil_im = background 
    imageConvert = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

#     Himage = Image.open(fileName %number)
    epd.display(epd.getbuffer(imageConvert))
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
    


    time.sleep(frameDelay)



epd.sleep()
    
epd7in5.epdconfig.module_exit()
exit()
