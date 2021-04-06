# SlowMovie

![](Extras/img.jpg)

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

Very Slow Movie Player using Python + Raspberry Pi

## Background

In December 2018, Bryan Boyer posted [“Creating a Very Slow Movie Player”](https://medium.com/s/story/very-slow-movie-player-499f76c48b62), an essay about light and Brasília and architecture in which Boyer builds an e-paper display that shows films at 24 frames per hour, rather than 24 frames per second so it takes about a year to play the 142 minutes of 2001: A Space Odyssey.

In August 2020, Tom Whitwell posted ["How to Build a Very Slow Movie Player for £120 in 2020"](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), with instructions on how to build a VSMP with the new [7.5-inch, Raspberry Pi-compatible e-paper display from Waveshare](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm).

SlowMovie is the code that runs a VSMP on your Raspberry Pi.

## Install

**Note:** These installation instructions assume you have access to your Raspberry Pi and that you have the hardware set up properly. See the [Medium post](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4) for more complete instructions.

SlowMovie requires [Python 3](https://www.python.org). It uses [FFmpeg](https://ffmpeg.org) via [ffmpeg-python](https://pypi.org/project/ffmpeg-python) for video processing, and [Pillow](https://python-pillow.org) for image processing.

On the Raspberry Pi:
0. Make sure SPI is enabled
  * Run `sudo raspi-config`
  * Navigate to `Interface Options` > `SPI`
1. Set up environment
  * Update package sources: `sudo apt update`
  * Make sure git is installed: `sudo apt install git`
  * Make sure pip is installed: `sudo apt install python3-pip`
  * Make sure setuptools is updated: `sudo pip3 install setuptools -U`
2. Clone repos
  * Waveshare e-paper: `git clone https://github.com/waveshare/e-Paper`
  * SlowMovie (this repo): `git clone https://github.com/TomWhitwell/SlowMovie`
3. Install e-paper drivers
  * Navigate to the e-paper driver directory: `cd e-Paper/RaspberryPi_JetsonNano/python`
  * Run `sudo python3 setup.py install`
  * Return to home directory: `cd ../../..`
4. Make sure dependencies are installed
  * `sudo apt install ffmpeg`
  * `sudo pip3 install configargparse
  * `sudo pip3 install ffmpeg-python`
  * `sudo pip3 install pillow`
5. Test it out
  * Navigate to the SlowMovie directory: `cd SlowMovie`
  * Run `python3 slowmovie.py`. If everything installed properly, this should start playing `test.mp4`, a clip from Psycho, which is already in the `Videos` directory.

## Usage

Put videos in the `Videos` directory. Use `python3 slowmovie.py -f <YOURFILENAME.EXT>` to start playing a movie of your choice.

If you want SlowMovie to start automatically when the device powered on:
* `sudo cp slowmovie.service /etc/systemd/system`
* `sudo systemctl daemon-reload`
* `sudo systemctl enable slowmovie`



The following options are available:

```
usage: slowmovie.py [-h] [-f FILE] [-d DELAY] [-i INCREMENT] [-s START] [-l]
                    [-r] [-R] [-D DIRECTORY] [-a] [-c CONTRAST]

Show a movie one frame at a time on an e-paper screen

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  filename of the video to start playing; otherwise play
                        the first file in the videos directory
  -d DELAY, --delay DELAY
                        delay in seconds between screen updates (default: 120)
  -i INCREMENT, --increment INCREMENT
                        advance INC frames each refresh (default: 4)
  -s START, --start START
                        start playing at a specific frame
  -l, --loop            loop a single video; otherwise play through the files
                        in the videos directory
  -r, --random-frames   choose a random frame every refresh
  -R, --random-file     play files in a random order; otherwise play them in
                        directory order
  -D DIRECTORY, --directory DIRECTORY
                        videos directory containing available videos to play
                        (default: Videos)
  -a, --adjust-delay    reduce delay by the amount of time taken to display a
                        frame
  -c CONTRAST, --contrast CONTRAST
                        adjust image contrast (default: 1.0)
```

## Maintainers

* [@qubist](https://github.com/qubist)
* [@robweber](https://github.com/robweber)
* [@missionfloyd](https://github.com/missionfloyd)

## Contributing

PRs accepted! Big diversions from core functionality or new features may fit better as a fork of the project.

### Contributors

* [@TomWhitwell](https://github.com/TomWhitwell)
* [@matpalm](https://github.com/matpalm)
* [@missionfloyd](https://github.com/missionfloyd)
* [@robweber](https://github.com/robweber)
* [@qubist](https://github.com/qubist)

## License

[MIT](/LICENSE)
