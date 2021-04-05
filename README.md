# SlowMovie

![](Extras/img.jpg)

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

Very Slow Movie Player using Python + Raspberry Pi

## Background

In December 2018, Bryan Boyer posted [“Creating a Very Slow Movie Player”](https://medium.com/s/story/very-slow-movie-player-499f76c48b62), an essay about light and Brasília and architecture in which Boyer builds an e-paper display that shows films at 24 frames per hour, rather than 24 frames per second so it takes about a year to play the 142 minutes of 2001: A Space Odyssey.

In August 2020, Tom Whitwell posted ["How to Build a Very Slow Movie Player for £120 in 2020"](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), with instructions on how to build a VSMP with the new [7.5-inch, Raspberry Pi-compatible e-paper display from Waveshare](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm).

SlowMovie is the code that runs a VSMP on a Raspberry Pi.

## Install

**Note:** These installation instructions assume you have access to your Raspberry Pi and that you have the hardware set up properly. See the [Medium post](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4) for more complete instructions.

SlowMovie requires [python3](https://www.python.org/). It uses [ffmpeg](https://ffmpeg.org/) via [ffmpeg-python](https://pypi.org/project/ffmpeg-python/) for video processing, and [Pillow](https://python-pillow.org/) for image processing. [ConfigArgParse](https://pypi.org/project/ConfigArgParse/) is used for configuration and argument handling.

On the Raspberry Pi:

0. Make sure SPI is turned on
    * run `sudo raspi-config`
    * Navigate to Interfacing Options > SPI
2. Install e-paper drivers
    * Clone the Waveshare repo: `git clone https://github.com/waveshare/e-Paper`
    * Go into the e-paper driver directory: `cd e-Paper/RaspberryPi_JetsonNano/python/`
    * Make sure pip3 is installed: `sudo apt install python3-pip`
    * Make sure setuptools is updated: `sudo pip3 install setuptools -U`
    * Install the drivers: `sudo python3 setup.py install`
    * Go back out of the e-paper directory: `cd ../../..`
2. Clone this repo
    * `git clone https://github.com/TomWhitwell/SlowMovie/`
    * Navigate to the new SlowMovie directory: `cd SlowMovie`
3. Make sure dependencies are installed
    * `sudo apt install ffmpeg`
    * `pip3 install ffmpeg-python`
    * `pip3 install pillow`
    * `pip3 install ConfigArgParse`
4. Test it out
    * Run `python3 slowmovie.py`. If everything's installed properly, this should start playing `test.mp4` (a clip from Psycho) which is already in the /Videos directory.

## Usage

Put videos in the /Videos directory. `python3 slowmovie.py start the program`.

The following options are available:

```
usage: slowmovie.py [-h] [-f FILE] [-R] [-r] [-D DIR] [-d DELAY]
                    [-i INCREMENT] [-s START] [-c CONTRAST] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Specify an MP4 file to play
  -R, --random-file     Play files in random order
  -r, --random          Display random frames
  -D DIR, --dir DIR     Select video directory
  -d DELAY, --delay DELAY
                        Time between updates, in seconds
  -i INCREMENT, --increment INCREMENT
                        Number of frames to advance on update
  -s START, --start START
                        Start at a specific frame
  -c CONTRAST, --contrast CONTRAST
                        Adjust image contrast (default: 1.0)
  -l, --loop            Loop single video.

Args that start with '--' (eg. -f) can also be set in a config file
(slowmovie.conf). Config file syntax allows: key=value, flag=true,
stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg is
specified in more than one place, then commandline values override config file
values which override defaults.
```

## Maintainers

* [@qubist](https://github.com/qubist)
* [@robweber](https://github.com/robweber)

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
