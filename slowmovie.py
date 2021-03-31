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
# from pprint import pprint

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

def generate_frame(in_filename, out_filename, time):
    try:
        (
            ffmpeg
            .input(in_filename, ss=time)
            .filter('scale', 'iw*sar', 'ih')
            .filter('scale', width, height, force_original_aspect_ratio=1)
            .filter('pad', width, height, -1, -1)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print('stdout:', e.stdout.decode('utf8'))
        print('stderr:', e.stderr.decode('utf8'))
        raise e

def is_vid(file):
    name, ext = os.path.splitext(file)
    return ext.lower() in fileTypes

def check_vid(file):
    if not is_vid(file):
        raise argparse.ArgumentTypeError(f"File '{file}' should be a file with one of the following supported extensions: {', '.join(fileTypes)}")
    return file

def check_dir(dir):
    if os.path.isdir(dir):
        return dir
    # Make default videos directory if it doesn't exist and it's needed
    elif dir == 'Videos':
        os.mkdir(dir)
    else:
        raise argparse.ArgumentTypeError(f"Directory '{dir}' could not be found")

# calculates how long it'll take to play a video that's videoLengthS seconds long.
# output valuev: 'd[ay]', 'h[our]', 'm[inute]', 's[econd]'
def estimate_playtime(delay, increment, videoLengthS, output):
    # assumes 24fps
    frames = videoLengthS*24

    seconds = (frames/increment)*delay
    minutes = seconds/60
    hours = minutes/60
    days = hours/24

    if output == 'd':
        return f'{days} day(s)'
    elif output == 'h':
        return f'{hours} hour(s)'
    elif output == 'm':
        return f'{minutes} minute(s)'
    elif output == 's':
        return f'{seconds} second(s)'
    else:
        raise ValueError

# Defaults
defaultIncrement = 4
defaultDelay = 120
defaultContrast = 1.0
defaultDirectory = 'Videos'

# types of video files understood
fileTypes = ['.mp4', '.mkv']

parser = argparse.ArgumentParser(description='Show a movie one frame at a time on an e-paper screen',
    epilog = 'After playback finishes, it restarts playing the same video')
parser.add_argument('-f', '--file',
    type = check_vid,
    help = 'filename of the video to start playing; otherwise play the first file in the videos directory')
parser.add_argument('-d', '--delay',
    type = float,
    default = defaultDelay,
    help = 'delay in seconds between screen updates (default: %(default)s)')
parser.add_argument('-i', '--increment',
    type = float,
    default = defaultIncrement,
    help = 'advance INC frames each refresh (default: %(default)s)')
parser.add_argument('-s', '--start',
    type = float,
    help = 'start playing at a specific frame')
parser.add_argument('-l', '--loop',
    action = 'store_true',
    help = 'loop a single video; otherwise play through the files in the videos directory')
parser.add_argument('-r', '--random-frames',
    action = 'store_true',
    help = 'choose a random frame every refresh')
parser.add_argument('-R', '--random-file',
    action = 'store_true',
    help = 'play files in a random order; otherwise play them in directory order')
parser.add_argument('-D', '--directory',
    type = check_dir,
    default = defaultDirectory,
    help = 'videos directory containing available videos to play')
parser.add_argument('-a', '--adjust-delay',
    action = 'store_true',
    help = 'reduce delay by the amount of time taken to display a frame')
parser.add_argument('-c', '--contrast',
    default = defaultContrast,
    type = float,
    help = 'adjust image contrast; a value of 1.0 is original contrast')
args = parser.parse_args()

# Move to the directory where this code is
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Name of videos directory and logs directory. Videos directory is specified by CLI --directory
viddir = args.directory
logdir = 'logs'

# Create logs directory if missing
if not os.path.isdir(logdir):
    os.mkdir(logdir)

if args.random_frames:
    print('In random mode')
else:
    print ('In play-through mode')

# Pick which video to play

# First, try the --file CLI argument...
currentVideo = args.file

# ...then try a random video, if --random-file was selected...
if not currentVideo and args.random_file:
    videos = list(filter(is_vid, os.listdir(viddir)))
    if videos:
        currentVideo = random.choice(videos)

# ...then try the nowPlaying file, which stores the currently-playing video...
if not currentVideo and os.path.isfile('nowPlaying'):
    with open('nowPlaying') as file:
        lastVideo = file.readline().strip()
        if os.path.isfile(lastVideo):
            currentVideo = lastVideo
        else:
            os.remove('nowPlaying')

# ...then just pick the first video in the videos directory...
if not currentVideo:
    # Scan through video directory until you find a video file
    videos = os.listdir(viddir)
    for file in videos:
        if is_vid(file):
            currentVideo = file
            break

# ...if none of those worked, exit.
if not currentVideo:
    print('No videos found in video directory')
    sys.exit()

with open('nowPlaying', 'w') as file:
    file.write(currentVideo)

# Keep track of what video we're playing and which ones are available
if not args.loop:
    videos = list(filter(is_vid, os.listdir(viddir)))
    fileIndex = videos.index(currentVideo)

print(f'Update interval: {args.delay}')
if not args.random_frames:
    print(f'Frame increment = {args.increment}')

print(f'With these settings, each minute of 24fps video will take {estimate_playtime(args.delay, args.increment, 60, "d")} to play.\nA 120-min movie will last {estimate_playtime(args.delay, args.increment, 120*60, "d")}.')

# make sure video file passed into CLI is in the videos directory
if args.file:
    if args.file in os.listdir(viddir):
        currentVideo = args.file
    else:
        print (f"File '{args.file}' not found")

# Initialise and clear the screen
epd = epd_driver.EPD()

width = epd.width
height = epd.height

# Check how many frames are in the video
probe = ffmpeg.probe(os.path.join(viddir, currentVideo))
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

print(f'There are {frameCount} frames in this video')

# Build name of log file
logfile = os.path.join(logdir, currentVideo + '.progress')

# Set up the start position based on CLI input or logfiles if either exists
if not args.random_frames:
    if args.start:
        currentFrame = clamp(args.start, 0, frameCount)
        print(f'Starting at frame {args.start}')
    elif os.path.isfile(logfile):
        # Log files store video progress
        # Get the stored position for this file from its log
        with open(logfile) as log:
            try:
                currentFrame = clamp(float(log.readline()), 0, frameCount)
            except Exception as e:
                # if there's no logfile, start at the beginning (we'll create one later)
                print(f'Reading logfile failed, caught following error: {e}. Starting at beginning of video.')
                currentFrame = 0
    else:
        currentFrame = 0

lastVideo = None

while True:
    # Print a message when starting a new video
    if lastVideo != currentVideo:
        print(f'Playing {currentVideo}')
        lastVideo = currentVideo

    # Note the time when starting to display so we can adjust for how long it takes later
    displayStartTime = time.perf_counter()

    epd.init()

    if args.random_frames:
        currentFrame = random.randint(0,frameCount)

    msTimecode = f'{currentFrame*41.666666}ms' # fixme replace with frametime, use real framerate

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it, and put it in memory as frame.bmp
    generate_frame(os.path.join(viddir, currentVideo), '/dev/shm/frame.bmp', msTimecode)

    # Open frame.bmp in PIL
    pil_im = Image.open('/dev/shm/frame.bmp')

    # Adjust contrast if specified
    if args.contrast != 1:
        enhancer = ImageEnhance.Contrast(pil_im)
        pil_im = enhancer.enhance(args.contrast)

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode = '1',dither = Image.FLOYDSTEINBERG)

    # display the image
    print(f'Displaying frame {int(currentFrame)} of {currentVideo} ({(currentFrame/frameCount)*100:.1f}%)')
    epd.display(epd.getbuffer(pil_im))

    # Increment the position
    if not args.random_frames:
        currentFrame += args.increment
        # If it's the end of the video
        if currentFrame > frameCount:
            if not args.loop:
                if args.random_file:
                    # Pick a new random video
                    currentVideo = random.choice(videos)
                else:
                    # Inrcrement fileIndex or wrap around
                    fileIndex += 1
                    if fileIndex >= len(videos):
                        fileIndex = 0

                    # Update currently playing video to be the incremented one
                    currentVideo = videos[fileIndex]

                # Note the new video we picked in nowPlaying file
                with open('nowPlaying', 'w') as file:
                    file.write(currentVideo)

                # Update logfile location
                logfile = os.path.join(logdir, currentVideo + '.progress')

                # Update video info for new video
                print('FIXME should be getting new video info, currently same framerate, etc maintained!')
                # FIXME get new video info
                # I'm gonna implement @robweber's implementation of video info, so I'm leaving it like this for a bit
                # framecount, framerate, frametime

            # Reset frame to 0 (this restars the same video if looping)
            currentFrame = 0

        with open(logfile, 'w') as log:
            log.write(str(currentFrame))

    epd.sleep()
    displayDelay = time.perf_counter() - displayStartTime
    if args.adjust_delay:
        time.sleep(max(args.delay - displayDelay, 0))
    else:
        time.sleep(args.delay)

epd.sleep()

epd7in5.epdconfig.module_exit()
exit()
