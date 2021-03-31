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

import os, time, sys, random, ffmpeg, argparse, signal
from PIL import Image, ImageEnhance

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

# Handle when the program is killed and exit gracefully
def signal_handler(signum, frame):
    print('\nExiting Program')

    # Call init to get gpio pins setup correctly and then exit properly
    epd_driver.epdconfig.module_init()
    epd_driver.epdconfig.module_exit()
    exit(0)

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

def get_video_info(filepath):
    probeInfo = ffmpeg.probe(filepath)

    stream = probeInfo['streams'][0]

    # Calculate framerate
    # https://github.com/fepegar/utils/commit/f52ab5152eaa5b8ceadefee172e985aaab3a9947#diff-521f42b0315f6bf8900be8407965552a8f6b32d9a22c09178c55be62b1bef4a2R23-R39
    r_fps = stream['r_frame_rate']
    try:
        num, denom = r_fps.split('/')
    except ValueError:
        # If r_fps isn't a fraction (does this happen?)
        num = r_fps
        denom = 1
    fps = float(num) / float(denom)

    # Calculate duration
    duration = float(probeInfo['format']['duration'])

    # Either get frame count or calculate it
    try:
        # Get frame count for .mp4s
        frameCount = int(stream['nb_frames'])
    except KeyError:
        # Calculate frame count for .mkvs (and maybe other formats?)
        frameCount = int(duration * fps)

    # Calculate frametime (ms each frame is displayed)
    frameTime = 1000 / fps

    return {
        'frame_count' : frameCount,
        'fps' : fps,
        'duration' : duration,
        'frame_time' : frameTime }

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

# Calculate how long it'll take to play a video.
# output value: 'd[ay]', 'h[our]', 'm[inute]', 's[econd]'
def estimate_runtime(delay, increment, videoLengthS, videoFPS, output):
    frames = videoLengthS*videoFPS

    seconds = (frames/increment)*delay
    minutes = seconds/60
    hours = minutes/60
    days = hours/24

    if output == 'd':
        return f'{days:.2f} day(s)'
    elif output == 'h':
        return f'{hours:.1f} hour(s)'
    elif output == 'm':
        return f'{minutes:.1f} minute(s)'
    elif output == 's':
        return f'{seconds:.1f} second(s)'
    elif output == 'a':
        return f'{seconds:.1f}s/{minutes:.1f}min/{hours:.1f}hr/{days:.2f}d'
    else:
        raise ValueError

# Defaults
defaultIncrement = 4
defaultDelay = 120
defaultContrast = 1.0
defaultDirectory = 'Videos'

# Compatible video file-extensions
fileTypes = ['.mp4', '.mkv']

parser = argparse.ArgumentParser(description='Show a movie one frame at a time on an e-paper screen')
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
    help = 'videos directory containing available videos to play (default: %(default)s)')
parser.add_argument('-a', '--adjust-delay',
    action = 'store_true',
    help = 'reduce delay by the amount of time taken to display a frame')
parser.add_argument('-c', '--contrast',
    default = defaultContrast,
    type = float,
    help = 'adjust image contrast; a value of 1.0 is original contrast')
args = parser.parse_args()

# Add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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

print(f'With these settings, each minute of 24fps video would take {estimate_runtime(args.delay, args.increment, 60, 24, "d")} to play.')
print(f'A 120-min movie would last {estimate_runtime(args.delay, args.increment, 120*60, 24, "d")}.')

# Make sure video file passed into CLI is in the videos directory
if args.file:
    if args.file in os.listdir(viddir):
        currentVideo = args.file
    else:
        print (f"File '{args.file}' not found")

# Set up EPD
epd = epd_driver.EPD()
width = epd.width
height = epd.height

# Build path to video
videoFilepath = os.path.join(viddir, currentVideo)

# Build name of log file
logfile = os.path.join(logdir, currentVideo + '.progress')

# Get the frame and duration infrmation of the video
videoInfo = get_video_info(videoFilepath)

# Set up the start position based on CLI input or logfiles if either exists
if not args.random_frames:
    if args.start:
        currentFrame = clamp(args.start, 0, videoInfo['frame_count'])
        print(f'Starting at frame {args.start}')
    elif os.path.isfile(logfile):
        # Log files store video progress
        # Get the stored position for this file from its log
        with open(logfile) as log:
            try:
                currentFrame = clamp(float(log.readline()), 0, videoInfo['frame_count'])
            except Exception as e:
                # If there's no logfile, start at the beginning (we'll create one later)
                print(f'Reading logfile failed, caught following error: {e}. Starting at beginning of video.')
                currentFrame = 0
    else:
        currentFrame = 0

# Set lastVideo so that first time through the loop, we'll print "Playing x"
lastVideo = None

while True:
    # Print a message when starting a new video
    if lastVideo != currentVideo:
        print(f"Playing '{currentVideo}'")
        print(f'Video info: {videoInfo["frame_count"]} frames, {videoInfo["fps"]:.3f}fps, duration: {videoInfo["duration"]}s')
        print(f'This video will take {estimate_runtime(args.delay, args.increment, videoInfo["duration"], videoInfo["fps"], "a")} to play.')
        lastVideo = currentVideo

    # Note the time when starting to display so we can adjust for how long it takes later
    displayStartTime = time.perf_counter()

    epd.init()

    if args.random_frames:
        currentFrame = random.randint(0,videoInfo['frame_count'])

    msTimecode = f'{currentFrame*videoInfo["frame_time"]}ms'

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it, and put it in memory as frame.bmp
    generate_frame(videoFilepath, '/dev/shm/frame.bmp', msTimecode)

    # Open frame.bmp in PIL
    pil_im = Image.open('/dev/shm/frame.bmp')

    # Adjust contrast if specified
    if args.contrast != 1:
        enhancer = ImageEnhance.Contrast(pil_im)
        pil_im = enhancer.enhance(args.contrast)

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode = '1',dither = Image.FLOYDSTEINBERG)

    # Display the image
    print(f'Displaying frame {int(currentFrame)} of {currentVideo} ({(currentFrame/videoInfo["frame_count"])*100:.1f}%)')
    epd.display(epd.getbuffer(pil_im))

    # Increment the position
    if not args.random_frames:
        currentFrame += args.increment
        # If it's the end of the video
        if currentFrame > videoInfo['frame_count']:
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
                # Update videoFilepath for newe video
                videoFilepath = os.path.join(viddir, currentVideo)
                # Update video info for new video
                videoInfo = get_video_info(videoFilepath)

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
