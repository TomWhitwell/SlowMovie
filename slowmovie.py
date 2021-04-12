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

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2 as epd_driver

# Defaults
defaultIncrement = 4
defaultDelay = 120
defaultContrast = 1.0
defaultDirectory = "Videos"

# Compatible video file-extensions
fileTypes = [".mp4", ".m4v", ".mkv"]


# Handle when the program is killed and exit gracefully
def exithandler(signum, frame):
    logger.info("Exiting Program")
    try:
        epd_driver.epdconfig.module_exit()
    finally:
        sys.exit()


# Add hooks for interrupt signal
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


# Used by configargparse to check that a file exists and is a compatible video
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


# Get framerate, frame count, duration, and frame-time of video via FFmpeg probe
def video_info(file):
    if file in videoInfos:
        info = videoInfos[file]
    else:
        probeInfo = ffmpeg.probe(file)
        stream = probeInfo["streams"][0]

        # Calculate framerate
        r_fps = stream["r_frame_rate"]
        fps = float(Fraction(r_fps))

        # Calculate duration
        duration = float(probeInfo["format"]["duration"])

        # Either get frame count or calculate it
        try:
            # Get frame count for .mp4s
            frameCount = int(stream["nb_frames"])
        except KeyError:
            # Calculate frame count for .mkvs (and maybe other formats?)
            frameCount = int(duration * fps)

        # Calculate frametime (ms each frame is displayed)
        frameTime = 1000 / fps

        info = {
            "frame_count": frameCount,
            "fps": fps,
            "duration": duration,
            "frame_time": frameTime}

        videoInfos[file] = info
    return info


# Returns the next video in the videos directory, or the first one if there's no current video
def get_next_video(viddir, currentVideo=None):
    # Only consider videos in the directory
    videos = sorted(list(filter(supported_filetype, os.listdir(viddir))))

    # Return None if there are no videos
    if not videos:
        return None

    if currentVideo:
        nextIndex = videos.index(currentVideo) + 1
        # If we're not wrapping around
        if not nextIndex >= len(videos):
            return os.path.join(viddir, videos[nextIndex])
    # Wrapping around or no current video: return first video
    return os.path.join(viddir, videos[0])


# Returns a random video from the videos directory
def get_random_video(viddir):
    videos = list(filter(supported_filetype, os.listdir(viddir)))
    if videos:
        return os.path.join(viddir, random.choice(videos))


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


parser = configargparse.ArgumentParser(default_config_files=["slowmovie.conf"])
parser.add_argument("-f", "--file", type=check_vid, help="video file to start playing; otherwise play the first file in the videos directory")
parser.add_argument("-R", "--random-file", action="store_true", help="play files in a random order; otherwise play them in directory order")
parser.add_argument("-r", "--random-frames", action="store_true", help="choose a random frame every refresh")
parser.add_argument("-D", "--directory", type=check_dir, help=f"directory containing available videos to play (default: {defaultDirectory})")
parser.add_argument("-d", "--delay", default=defaultDelay, type=int, help="delay in seconds between screen updates (default: %(default)s)")
parser.add_argument("-i", "--increment", default=defaultIncrement, type=int, help="advance INCREMENT frames each refresh (default: %(default)s)")
parser.add_argument("-s", "--start", type=int, help="start playing at a specific frame")
parser.add_argument("-c", "--contrast", default=defaultContrast, type=float, help="adjust image contrast (default: %(default)s)")
parser.add_argument("-l", "--loop", action="store_true", help="loop a single video; otherwise play through the files in the videos directory")
parser.add_argument("-o", "--loglevel", default="INFO", type=str.upper, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="minimum importance-level of messages saved to the logfile (default: %(default)s)")
args = parser.parse_args()

# Move to the directory where this code is
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

fileHandler = logging.FileHandler("slowmovie.log")
fileHandler.setLevel(getattr(logging, args.loglevel))
fileHandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(consoleHandler)

# Set path of Videos directory and logs directory. Videos directory can be specified by CLI --directory
if args.directory:
    viddir = args.directory
else:
    viddir = defaultDirectory
progressdir = "progress"

# Create progress and Videos directories if missing
if not os.path.isdir(progressdir):
    os.mkdir(progressdir)
if not os.path.isdir(viddir):
    os.mkdir(viddir)

# Move leftover progress files
if os.path.isdir("logs"):
    for f in os.listdir("logs"):
        if f.endswith(".progress"):
            os.rename(os.path.join("logs", f), os.path.join(progressdir, f))
    # Remove old logs dir if empty
    try:
        os.rmdir("logs")
    except OSError:
        pass

# Pick which video to play
logger.debug("Picking which video to play...")

# First, try the --file CLI argument...
logger.debug("...trying the --file argument...")
currentVideo = args.file

# ...then try a random video, if --random-file was selected...
if not currentVideo and args.random_file:
    logger.debug("...random-file mode: trying to pick a random video...")
    currentVideo = get_random_video(viddir)

# ...then try the nowPlaying file, which stores the last played video...
if not currentVideo and os.path.isfile("nowPlaying"):
    logger.debug("...trying the video in the nowPlaying file...")
    with open("nowPlaying") as file:
        lastVideo = os.path.abspath(file.readline().strip())
    if os.path.isfile(lastVideo):
        if os.path.dirname(lastVideo) == os.path.abspath(viddir) or not args.directory:
            currentVideo = lastVideo
    else:
        logger.warning(f"'{lastVideo}' read from nowPlaying file couldn't be found. Removing nowPlaying directory for recreation.")
        os.remove("nowPlaying")

# ...then just pick the first video in the videos directory...
if not currentVideo:
    logger.debug("...trying to pick the first video in the directory...")
    currentVideo = get_next_video(viddir)

# ...if none of those worked, exit.
if not currentVideo:
    logger.critical("No videos found")
    sys.exit()

logger.debug(f"...picked '{currentVideo}'!")

logger.info(f"Update interval: {args.delay}")
if not args.random_frames:
    logger.info(f"Frame increment: {args.increment}")

# Write the current video to the nowPlaying file
with open("nowPlaying", "w") as file:
    file.write(os.path.abspath(currentVideo))

videoFilename = os.path.basename(currentVideo)
viddir = os.path.dirname(currentVideo)

progressfile = os.path.join(progressdir, f"{videoFilename}.progress")

# Set up e-Paper display
epd = epd_driver.EPD()
width = epd.width
height = epd.height

videoInfos = {}
videoInfo = video_info(currentVideo)

# Set up the start position based on CLI input or progressfiles if either exists
if not args.random_frames:
    if args.start:
        currentFrame = clamp(args.start, 0, videoInfo["frame_count"])
        logger.info(f"Starting at frame {currentFrame}")
    elif (os.path.isfile(progressfile)):
        # Read current frame from progressfile
        with open(progressfile) as log:
            try:
                currentFrame = int(log.readline())
                currentFrame = clamp(currentFrame, 0, videoInfo["frame_count"])
                logger.info(f"Resuming at frame {currentFrame}")
            except ValueError:
                currentFrame = 0
    else:
        currentFrame = 0

# Initialize lastVideo so that first time through the loop, we'll print "Playing x"
lastVideo = None

while True:
    if lastVideo != currentVideo:
        # Print a message when starting a new video
        logger.info(f"Playing '{videoFilename}'")
        logger.info(f"Video info: {videoInfo['frame_count']} frames, {videoInfo['fps']:.3f}fps, duration: {videoInfo['duration']}s")
        if not args.random_frames:
            logger.debug(f"This video will take {estimate_runtime(args.delay, args.increment, videoInfo['frame_count'] - currentFrame)} to play.")

        lastVideo = currentVideo

    # Note the time when starting to display so later we can sleep for the delay value minus how long this takes
    timeStart = time.perf_counter()
    epd.init()

    if args.random_frames:
        currentFrame = random.randint(0, videoInfo["frame_count"])

    msTimecode = "%dms" % (currentFrame * videoInfo["frame_time"])

    # Use ffmpeg to extract a frame from the movie, letterbox/pillarbox it, and put it in memory as frame.bmp
    generate_frame(currentVideo, "/dev/shm/frame.bmp", msTimecode)

    # Open frame.bmp in PIL
    pil_im = Image.open("/dev/shm/frame.bmp")

    # Adjust contrast if specified
    if args.contrast != 1:
        enhancer = ImageEnhance.Contrast(pil_im)
        pil_im = enhancer.enhance(args.contrast)

    # Display the image
    logger.debug(f"Displaying frame {int(currentFrame)} of {videoFilename} ({(currentFrame/videoInfo['frame_count'])*100:.1f}%)")
    epd.display(epd.getbuffer(pil_im))

    # Increment the position
    if not args.random_frames:
        currentFrame += args.increment
        # If it's the end of the video
        if currentFrame > videoInfo["frame_count"]:
            if not args.loop:
                if args.random_file:
                    # Pick a new random video
                    currentVideo = get_random_video(viddir)
                else:
                    # Update currently playing video to be the next one in the Videos directory
                    currentVideo = get_next_video(viddir, videoFilename)

                # Note new video in nowPlaying file
                with open("nowPlaying", "w") as file:
                    file.write(os.path.abspath(currentVideo))

                # Update progressfile location
                progressfile = os.path.join(progressdir, f"{videoFilename}.progress")
                # Update videoFilepath for new video
                videoFilename = os.path.basename(currentVideo)
                # Update video info for new video
                videoInfo = video_info(currentVideo)

            # Reset frame to 0 (this restarts the same video if looping)
            currentFrame = 0

        # Log the new location in the proper progressfile
        with open(progressfile, "w") as log:
            log.write(str(currentFrame))

    epd.sleep()

    # Adjust sleep delay to account for the time since we started updating this frame.
    timeDiff = time.perf_counter() - timeStart
    time.sleep(max(args.delay - timeDiff, 0))
