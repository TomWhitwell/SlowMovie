# SlowMovie

![](Extras/img.jpg)

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

Very Slow Movie Player using Python + Raspberry Pi

## Table Of Contents

- [Background](#background)
- [Install](#install)
  - [Automated Installation](#automated-installation)
  - [Manual Installation](#manual-installation)
- [Usage](#usage)
  - [E-ink Display Customization](#e-ink-display-customization)
  - [Running as a Service](#running-as-a-service)
- [Maintainers](#maintainers)
- [Contributors](#contributors)
- [License](#license)

## Background

In December 2018, Bryan Boyer posted [“Creating a Very Slow Movie Player”](https://medium.com/s/story/very-slow-movie-player-499f76c48b62), an essay about light and Brasília and architecture in which Boyer builds an e-paper display that shows films at 24 frames per hour, rather than 24 frames per second so it takes about a year to play the 142 minutes of _2001: A Space Odyssey_.

In August 2020, Tom Whitwell posted ["How to Build a Very Slow Movie Player for £120 in 2020"](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), with instructions on how to build a VSMP with the new [7.5-inch, Raspberry Pi-compatible e-paper display from Waveshare](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm).

SlowMovie is the code that runs a VSMP on a Raspberry Pi.

## Install

**Note:** These installation instructions assume you have access to your Raspberry Pi and that you have the hardware set up properly. See the [Medium post](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4) for more complete instructions.

SlowMovie requires [Python 3](https://www.python.org). It uses [FFmpeg](https://ffmpeg.org) via [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) for video processing, [Pillow](https://python-pillow.org) for image processing, and [Omni-EPD](https://github.com/robweber/omni-epd) for loading the correct e-ink display driver. [ConfigArgParse](https://github.com/bw2/ConfigArgParse) is used for configuration and argument handling.

### Automated installation

You can quickly install this repository and all required libraries via an install script. This is a simple way to get started if you're not as comfortable with the command line.

To run the install script, open your terminal, copy-paste the following command in, and hit enter.

    bash <(curl https://raw.githubusercontent.com/TomWhitwell/SlowMovie/main/Install/install.sh)

You'll be presented with 4 options when you run the script:

1. **Install/Upgrade SlowMovie** - download the repository and install/update any libraries needed
2. **Install SlowMovie Service** - run the commands install the SlowMovie service file as described below
3. **Uninstall SlowMovie Service** - uninstall the SlowMovie service
4. **Exit**

For first-time automated installation, choose 1: Install/Upgrade SlowMovie. When prompted, you can choose "yes" to have the SlowMovie service installed as well which will enable playback to start automatically when the device is powered on or rebooted.

### Manual installation

_Note that the `omni-epd` package installs Waveshare and Inky EPD driver libraries._
On the Raspberry Pi:

0. Make sure SPI is enabled
   * Run `sudo raspi-config`
   * Navigate to `Interface Options` > `SPI`
   * Select `<Finish>` to exit. Reboot if prompted.
1. Set up environment
   * Update package sources: `sudo apt update`
   * Make sure git is installed: `sudo apt install git`
   * Make sure pip is installed: `sudo apt install python3-pip`
2. Install Waveshare e-paper drivers
   * `pip3 install "git+https://github.com/waveshare/e-Paper.git#subdirectory=RaspberryPi_JetsonNano/python&egg=waveshare-epd"`
3. Clone this repo
   * `git clone https://github.com/TomWhitwell/SlowMovie`
   * Navigate to the new SlowMovie directory: `cd SlowMovie/`
   * Copy the default configuration file: `cp Install/slowmovie-default.conf slowmovie.conf`
4. Make sure dependencies are installed
   * `sudo apt install ffmpeg`
   * `pip3 install ffmpeg-python`
   * `pip3 install pillow`
   * `pip3 install ConfigArgParse`
   * `pip3 install git+https://github.com/robweber/omni-epd.git#egg=omni-epd`
5. Test it out
   * Run `python3 slowmovie.py`. If everything's installed properly, this should start playing `test.mp4` (a clip from _Psycho_) from the `Videos` directory.

## Usage

### Running from the shell

Put videos in the `Videos` directory. Run `python3 slowmovie.py` to start the program.

The following options are available:

```
usage: slowmovie.py [-h] [-f FILE] [-D DIRECTORY] [-l] [-R]
                    [-o {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-r] [-d DELAY]
                    [-i INCREMENT] [-s START] [-F] [-S | -t] [-e EPD]
                    [-c CONTRAST] [-C]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  video file to start playing; otherwise play the first
                        file in the videos directory
  -D DIRECTORY, --directory DIRECTORY
                        directory containing available videos to play
                        (default: Videos)
  -l, --loop            loop a single video; otherwise play through the files
                        in the videos directory
  -R, --random-file     play files in a random order; otherwise play them in
                        directory order
  -o {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        minimum importance-level of messages displayed and
                        saved to the logfile (default: INFO)

Frame Update Args:
  arguments that control frame updates and display

  -r, --random-frames   choose a random frame every refresh
  -d DELAY, --delay DELAY
                        delay in seconds between screen updates (default: 120)
  -i INCREMENT, --increment INCREMENT
                        advance INCREMENT frames each refresh (default: 4)
  -s START, --start START
                        start playing at a specific frame
  -F, --fullscreen      expand image to fill display
  -S, --subtitles       display SRT subtitles
  -t, --timecode        display video timecode

EPD Args:
  arguments to select and modify the e-Ink display

  -e EPD, --epd EPD     the name of the display device driver to use
  -c CONTRAST, --contrast CONTRAST
                        adjust image contrast (default: 1.0)
  -C, --clear           clear display on exit

Args that start with '--' (eg. -f) can also be set in a config file
(slowmovie.conf). Config file syntax allows: key=value, flag=true,
stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg is
specified in more than one place, then commandline values override config file
values which override defaults.
```

### E-ink Display Customization

The guide for this program uses the [7.5-inch Waveshare display](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm), this is the device driver loaded by default in the `slowmovie.conf` file. It is possible to specify other devices by editing the file or using the command line `-e` option. You can view a list of compatible e-ink devices on the [Omni-EPD repo](https://github.com/robweber/omni-epd/blob/main/README.md#displays-implemented).

Customizing other options of the display is also possible by creating a file called `omni-epd.ini` in the SlowMovie directory. Common options for this file are listed below with a full explanation of all options available.

```
[Display]
rotate=0  # rotate final image written to display by X degrees [0-360]
flip_horizontal=False  # flip image horizontally
flip_vertical=False  # flip image vertically

[Image Enhancements]
contrast=1  # adjust image contrast, 1 = no adjustment
brightness=1  # adjust image brightness, 1 = no adjustment
sharpness=1  # adjust image sharpness, 1 = no adjustment
```

### Running as a service

SlowMovie can run as a service. To set this up you can either use option 2 from the install script ( [see above](https://github.com/TomWhitwell/SlowMovie#automated-installation) ) or from the SlowMovie directory run the following:

```
envsubst <slowmovie.service.template > slowmovie.service
sudo mv slowmovie.service /etc/systemd/system
sudo systemctl daemon-reload
```

When running as a service, you can use the config file ([see above](https://github.com/TomWhitwell/SlowMovie/#running-from-the-shell)) to pick which movie to play and set all other options.  

Now you can use the `systemctl` command to start and stop the program, and enable auto-start on boot:

| Command                                    | Effect                                      |
|:-------------------------------------------|:--------------------------------------------|
| `sudo systemctl start slowmovie`           | Start the SlowMovie service playing         |
| `sudo systemctl stop slowmovie`            | Stop the SlowMovie service                  |
| `sudo systemctl enable slowmovie`          | Enable the service auto-starting on boot    |
| `sudo systemctl disable slowmovie`         | Disable the service auto-starting on boot   |
| `systemctl status slowmovie`               | Display the status of the SlowMovie service |
| `tail -f ~/SlowMovie/slowmovie.log`    | Show the logs for the SlowMovie service     |

So, if you want SlowMovie to start automatically when the device is powered on, run:

```
sudo systemctl enable slowmovie
```

And if something goes wrong, the first step is to check the logs for an error message. The command above will show the last few lines of the log file but you can view the entire file located at `~/SlowMovie/slowmovie.log` with any text editor.

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
