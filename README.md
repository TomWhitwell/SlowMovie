# SlowMovie

![](Extras/img.jpg)

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

Very Slow Movie Player using Python + Raspberry Pi

## Background

In December 2018, Bryan Boyer posted [“Creating a Very Slow Movie Player”](https://medium.com/s/story/very-slow-movie-player-499f76c48b62), an essay about light and Brasília and architecture in which Boyer builds an e-paper display that shows films at 24 frames per hour, rather than 24 frames per second so it takes about a year to play the 142 minutes of _2001: A Space Odyssey_.

In August 2020, Tom Whitwell posted ["How to Build a Very Slow Movie Player for £120 in 2020"](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), with instructions on how to build a VSMP with the new [7.5-inch, Raspberry Pi-compatible e-paper display from Waveshare](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm).

SlowMovie is the code that runs a VSMP on a Raspberry Pi.

## Install

**Note:** These installation instructions assume you have access to your Raspberry Pi and that you have the hardware set up properly. See the [Medium post](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4) for more complete instructions.

SlowMovie requires [Python 3](https://www.python.org). It uses [FFmpeg](https://ffmpeg.org) via [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) for video processing, [Pillow](https://python-pillow.org) for image processing, and [Omni-EPD](https://github.com/robweber/omni-epd) for loading the correct e-ink display driver. [ConfigArgParse](https://github.com/bw2/ConfigArgParse) is used for configuration and argument handling.

On the Raspberry Pi:

0. Make sure SPI is enabled
   * Run `sudo raspi-config`
   * Navigate to `Interface Options` > `SPI`
   * Select `<Finish>` to exit. Reboot if prompted.
1. Set up environment
   * Update package sources: `sudo apt update`
   * Make sure git is installed: `sudo apt install git`
   * Make sure pip is installed: `sudo apt install python3-pip`
   * Make sure setuptools is updated: `sudo pip3 install setuptools -U`
2. Install e-paper drivers
   * Clone the Waveshare repo: `git clone https://github.com/waveshare/e-Paper`
   * Go into the e-paper driver directory: `cd e-Paper/RaspberryPi_JetsonNano/python/`
   * Install the drivers: `sudo python3 setup.py install`
   * Go back out of the e-paper directory: `cd ../../..`
3. Clone this repo
   * `git clone https://github.com/TomWhitwell/SlowMovie`
   * Navigate to the new SlowMovie directory: `cd SlowMovie/`
4. Make sure dependencies are installed
   * `sudo apt install ffmpeg`
   * `sudo pip3 install ffmpeg-python`
   * `sudo pip3 install pillow`
   * `sudo pip3 install ConfigArgParse`
   * `sudo pip3 install git+https://github.com/robweber/omni-epd.git#egg=omni-epd'
5. Test it out
   * Run `python3 slowmovie.py`. If everything's installed properly, this should start playing `test.mp4` (a clip from _Psycho_) from the `Videos` directory.

## Usage

### Running from the shell

Put videos in the `Videos` directory. Run `python3 slowmovie.py` to start the program.

The following options are available:

```
usage: slowmovie.py [-h] [-f FILE] [-R] [-r] [-D DIRECTORY] [-d DELAY]
                    [-i INCREMENT] [-s START] [-c CONTRAST] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  video file to start playing; otherwise play the first
                        file in the videos directory
  -R, --random-file     play files in a random order; otherwise play them in
                        directory order
  -r, --random-frames   choose a random frame every refresh
  -D DIRECTORY, --directory DIRECTORY
                        videos directory containing available videos to play
                        (default: Videos)
  -d DELAY, --delay DELAY
                        delay in seconds between screen updates (default: 120)
  -i INCREMENT, --increment INCREMENT
                        advance INCREMENT frames each refresh (default: 4)
  -s START, --start START
                        start playing at a specific frame
  -c CONTRAST, --contrast CONTRAST
                        adjust image contrast (default: 1.0)
  -l, --loop            loop a single video; otherwise play through the files
                        in the videos directory
  -e, --epd             the name of the display device driver to use (default: waveshare_epd.epd7in5_V2)
  -o {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                         minimum importance-level of messages displayed and
                         saved to the logfile (default: INFO)

Args that start with '--' (eg. -f) can also be set in a config file
(slowmovie.conf). Config file syntax allows: key=value, flag=true,
stuff=[a,b,c] (for details, see syntax at https://pypi.org/project/ConfigArgParse).
If an arg is specified in more than one place, then commandline values override
config file values, which in turn override defaults.
```

### E-ink Display Drivers

The guide for this program uses the [7.5-inch Waveshare display](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm), this is the device driver loaded by default. It is possible to specify other devices using the command line `-e` option. Currently most Waveshare displays are compatible but we hope to have others in the near future. An example of running Slowmovie with a 4.2inch Waveshare display instead would be:

```
python3 slowmovie.py -e waveshare_epd.epd4in2b_V2

```

You can view a list of compatible e-ink devices on the [Omni-EPD repo](https://github.com/robweber/omni-epd/blob/main/README.md#displays-implemented).

### Running as a service

SlowMovie can run as a service. To set this up, from the SlowMovie directory run the following:

```
sudo cp slowmovie.service /etc/systemd/system
sudo systemctl daemon-reload
```

Now you can use the `systemctl` command to start and stop the program, and enable auto-start on boot:

| Command                                    | Effect                                      |
|:-------------------------------------------|:--------------------------------------------|
| `sudo systemctl start slowmovie`           | Start the SlowMovie service playing         |
| `sudo systemctl stop slowmovie`            | Stop the SlowMovie service                  |
| `sudo systemctl enable slowmovie`          | Enable the service auto-starting on boot    |
| `sudo systemctl disable slowmovie`         | Disable the service auto-starting on boot   |
| `systemctl status slowmovie`               | Display the status of the SlowMovie service |
| `tail -f /home/pi/SlowMovie/slowmovie.log` | Show the logs for the SlowMovie service     |

So, if you want SlowMovie to start automatically when the device is powered on, run:

```
sudo systemctl enable slowmovie
```

And if something goes wrong, the first step is to check the logs for an error message. The command above will show the last few lines of the log file but you can view the entire file located at `/home/pi/SlowMovie/slowmovie.log` with any text editor.

## Maintainers

* [@qubist](https://github.com/qubist)
* [@robweber](https://github.com/robweber)
* [@missionfloyd](https://github.com/missionfloyd)

## Contributing

PRs accepted! Big diversions from core functionality or new features may fit better as a fork of the project.

Please read our [contributing guidelines](/.github/CONTRIBUTING.md) before submitting an issue or pull request.

### Contributors

* [@TomWhitwell](https://github.com/TomWhitwell)
* [@matpalm](https://github.com/matpalm)
* [@missionfloyd](https://github.com/missionfloyd)
* [@robweber](https://github.com/robweber)
* [@qubist](https://github.com/qubist)

## License

[MIT](/LICENSE)
