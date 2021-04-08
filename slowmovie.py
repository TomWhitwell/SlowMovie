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

import os
import time
import sys
import random
import signal
import logging
import ffmpeg
import configargparse
from PIL import Image, ImageEnhance
from fractions import Fraction

logger = logging.getLogger()
logger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("slowmovie.log")
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(consoleHandler)

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

# Defaults
defaultIncrement = 4
defaultDelay = 120
defaultContrast = 1.0
defaultDirectory = "Videos"

fileTypes = [".mp4", ".m4v", ".mkv"]


def exithandler(signum, frame):
    try:
        epd_driver.epdconfig.module_exit()
    finally:
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


def check_vid(value):
    if not os.path.isfile(value):
        raise configargparse.ArgumentTypeError("File '%s' does not exist" % value)
    if not supported_filetype(value):
        raise configargparse.ArgumentTypeError(f"File '{file}' should be a file with one of the following supported extensions: {', '.join(fileTypes)}")
    return value


def check_dir(value):
    if os.path.isdir(value):
        return value
    else:
        raise configargparse.ArgumentTypeError("Directory '%s' does not exist" % value)


def supported_filetype(file):
    _, ext = os.path.splitext(file)
    return ext.lower() in fileTypes


def video_info(file):
    if file in videoInfos:
        info = videoInfos[file]
    else:
        probeInfo = ffmpeg.probe(file)
        stream = probeInfo['streams'][0]

        # Calculate framerate
        r_fps = stream['r_frame_rate']
        fps = float(Fraction(r_fps))

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

        info = {
            'frame_count': frameCount,
            'fps': fps,
            'duration': duration,
            'frame_time': frameTime}

        videoInfos[file] = info
    return info


# Calculate how long it'll take to play a video.
# output value: "d[ay]", "h[our]", "m[inute]", "s[econd]", "all"; omit for an automatic guess
def estimate_runtime(delay, increment, frames, output="guess"):
    # Recurse to generate all estimates in one string
    if output == "all":
        return f"{estimate_runtime(delay, increment, frames, 's')} / {estimate_runtime(delay, increment, frames, 'm')} / {estimate_runtime(delay, increment, frames, 'h')} / {estimate_runtime(delay, increment, frames, 'd')}"

    # Calculate runtime lengths in different units
    seconds = (frames / increment) * delay
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24

    if output == "guess":
        # Choose the biggest units that result in a quantity greater than 1
        for length, outputGuess in [(days, "d"), (hours, "h"), (minutes, "m"), (seconds, "s")]:
            if length > 1:
                return estimate_runtime(delay, increment, frames, outputGuess)

    # Base cases, each returning runtime in a specific unit
    if output == "d":
        return f"{days:.2f} day(s)"
    elif output == "h":
        return f"{hours:.1f} hour(s)"
    elif output == "m":
        return f"{minutes:.1f} minute(s)"
    elif output == "s":
        return f"{seconds:.1f} second(s)"
    else:
        raise ValueError


os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = configargparse.ArgumentParser(default_config_files=["slowmovie.conf"])
parser.add_argument("-f", "--file", type=check_vid, help="video file to start playing; otherwise play the first file in the videos directory")
parser.add_argument("-R", "--random-file", action="store_true", help="play files in a random order; otherwise play them in directory order")
parser.add_argument("-r", "--random-frames", action="store_true", help="choose a random frame every refresh")
parser.add_argument("-D", "--directory", type=check_dir, help="directory containing available videos to play (default: %(default)s)")
parser.add_argument("-d", "--delay", default=defaultDelay, type=int, help="delay in seconds between screen updates (default: %(default)s)")
parser.add_argument("-i", "--increment", default=defaultIncrement, type=int, help="advance INCREMENT frames each refresh (default: %(default)s)")
parser.add_argument("-s", "--start", type=int, help="start playing at a specific frame")
parser.add_argument("-c", "--contrast", default=defaultContrast, type=float, help="adjust image contrast (default: %(default)s)")
parser.add_argument("-l", "--loop", action="store_true", help="loop a single video; otherwise play through the files in the videos directory")
parser.add_argument("--service", action="store_true", help=configargparse.SUPPRESS)
args = parser.parse_args()

if args.directory:
    viddir = args.directory
else:
    viddir = defaultDirectory

logdir = "logs"

if not os.path.isdir(logdir):
    os.mkdir(logdir)
if not os.path.isdir(viddir):
    os.mkdir(viddir)

# First we try the file argument...
currentVideo = args.file

# ...then a random video, if selected...
if not currentVideo and args.random_file:
    videos = list(filter(supported_filetype, os.listdir(viddir)))
    if videos:
        currentVideo = os.path.join(viddir, random.choice(videos))

# ...then the last played file...
if not currentVideo and os.path.isfile("nowPlaying") and not args.directory:
    with open("nowPlaying") as file:
        lastVideo = file.readline().strip()
        if os.path.isfile(lastVideo):
            currentVideo = lastVideo
        else:
            os.remove("nowPlaying")

# ...then we look in the videos folder.
if not currentVideo:
    videos = sorted(os.listdir(viddir))
    for file in videos:
        if supported_filetype(file):
            currentVideo = os.path.join(viddir, file)
            break

# If none of the above worked, exit.
if not currentVideo:
    logger.critical("No videos found")
    sys.exit()

logger.info("Update interval: " + str(args.delay))
if not args.random_frames:
    logger.info("Frame increment: " + str(args.increment))

with open("nowPlaying", "w") as file:
    file.write(os.path.abspath(currentVideo))

videoFilename = os.path.basename(currentVideo)

if not args.loop:
    viddir = os.path.dirname(currentVideo)
    videos = sorted(list(filter(supported_filetype, os.listdir(viddir))))
    fileIndex = videos.index(videoFilename)

logfile = os.path.join(logdir, videoFilename + ".progress")

epd = epd_driver.EPD()
width = epd.width
height = epd.height

videoInfos = {}
videoInfo = video_info(currentVideo)

if not args.random_frames:
    if args.start:
        currentFrame = clamp(args.start, 0, videoInfo["frame_count"])
        logger.info("Starting at frame " + str(currentFrame))
    elif (os.path.isfile(logfile)):
        # Read current frame from logfile
        with open(logfile) as log:
            try:
                currentFrame = int(log.readline())
                currentFrame = clamp(currentFrame, 0, videoInfo["frame_count"])
            except ValueError:
                currentFrame = 0
    else:
        currentFrame = 0

lastVideo = None

while 1:
    if lastVideo != currentVideo:
        logger.info(f"Playing '{videoFilename}'")
        logger.info(f"Video info: {videoInfo['frame_count']} frames, {videoInfo['fps']:.3f}fps, duration: {videoInfo['duration']}s")
        if not args.random_frames:
            logger.info(f"This video will take {estimate_runtime(args.delay, args.increment, videoInfo['frame_count'])} to play.")
        lastVideo = currentVideo

    timeStart = time.perf_counter()
    epd.init()

    if args.random_frames:
        currentFrame = random.randint(0, videoInfo["frame_count"])

    msTimecode = "%dms" % (currentFrame * videoInfo["frame_time"])

    # Use ffmpeg to extract a frame from the movie, letterbox/pillarbox it and save it as frame.bmp
    generate_frame(currentVideo, "/dev/shm/frame.bmp", msTimecode)

    # Open frame.bmp in PIL
    pil_im = Image.open("/dev/shm/frame.bmp")

    if args.contrast != 1:
        enhancer = ImageEnhance.Contrast(pil_im)
        pil_im = enhancer.enhance(args.contrast)

    # Dither the image into a 1 bit bitmap
    # pil_im = pil_im.convert(mode = "1", dither = Image.FLOYDSTEINBERG)

    # display the image
    logger.info(f"Displaying frame {int(currentFrame)} of {videoFilename} ({(currentFrame/videoInfo['frame_count'])*100:.1f}%)")
    epd.display(epd.getbuffer(pil_im))

    if not args.random_frames:
        currentFrame += args.increment
        if currentFrame > videoInfo["frame_count"]:
            # end of video
            if not args.loop:
                if args.random_file:
                    currentVideo = os.path.join(viddir, random.choice(videos))
                else:
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
                videoInfo = video_info(currentVideo)

            currentFrame = 0

        with open(logfile, "w") as log:
            log.write(str(currentFrame))

    epd.sleep()
    timeDiff = time.perf_counter() - timeStart
    time.sleep(max(args.delay - timeDiff, 0))
