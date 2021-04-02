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

import os, time, sys, random, ffmpeg, signal
from PIL import Image

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

# Handle when the program is killed and exit gracefully
def signal_handler(signum, frame):
    print('\nExiting Program')

    # Call init to get gpio pins setup correctly and then exit properly
    epd_driver.epdconfig.module_init()
    epd_driver.epdconfig.module_exit()
    exit(0)

def generate_frame(in_filename, out_filename, timecode):
    try:
        (
            ffmpeg
            .input(in_filename, ss=timecode)
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

# Returns a random video from the videos directory
def get_random_video(viddir):
    videos = list(filter(is_vid, os.listdir(viddir)))
    if videos:
        return random.choice(videos)

def is_vid(file):
    name, ext = os.path.splitext(file)
    return ext.lower() in fileTypes

# Compatible video file-extensions
fileTypes = ['.mp4', '.mkv']

# Path to your video folder
viddir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../Videos/')

# Add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Move to the directory where this code is
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Pick a random video to play
currentVideo = get_random_video(viddir)

# ...if none of those worked, exit.
if not currentVideo:
    print('No videos found in video directory')
    sys.exit()

# Set up EPD
epd = epd_driver.EPD()
width = epd.width
height = epd.height

# Build path to video
videoFilepath = os.path.join(viddir, currentVideo)

# Get the frame and duration infrmation of the video
videoInfo = get_video_info(videoFilepath)

print(f"Playing '{currentVideo}'")

while True:

    # Initialize the screen
    epd.init()

    # Chose a random frame from the video
    currentFrame = random.randint(0,videoInfo['frame_count'])

    # Convert that frame into a timecode
    msTimecode = f'{currentFrame*videoInfo["frame_time"]}ms'

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it, and put it in memory as frame.bmp
    generate_frame(videoFilepath, '/dev/shm/frame.bmp', msTimecode)

    # Open frame.bmp in PIL
    pil_im = Image.open('/dev/shm/frame.bmp')

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode = '1',dither = Image.FLOYDSTEINBERG)

    # Display the image
    print(f'Displaying frame {int(currentFrame)} of {currentVideo}')
    epd.display(epd.getbuffer(pil_im))

    # Put screen to sleep and wait 10 seconds
    epd.sleep()
    time.sleep(10)
