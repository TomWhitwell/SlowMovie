#!/bin/bash -e

GIT_REPO=https://github.com/TomWhitwell/SlowMovie
GIT_BRANCH=master
PYTHON_VERSION=3
SKIP_DEPS=false

# color code variables
RED="\e[0;91m"
YELLOW="\e[0;93m"
RESET="\e[0m"

# file paths
SERVICE_DIR=/etc/systemd/system
SERVICE_FILE=slowmovie.service

function install_linux_packages(){
  sudo apt-get update

  sudo apt-get install -y ffmpeg git python3-pip
}

function install_python_packages(){


  sudo pip3 install setuptools -U
  sudo pip3 install -r $LOCAL_DIR/Install/requirements.txt
}

function build_python_libraries(){
  WAVESHARE_DIR=/home/pi/e-Paper

  if [ -d "${WAVESHARE_DIR}" ]; then
    echo -e "Updating Waveshare Drivers"
    cd $WAVESHARE_DIR
    git fetch
    git pull
  else
    echo -e "Installing Waveshare Drivers"
    git clone https://github.com/waveshare/e-Paper
  fi

  echo -e "${YELLOW}Be patient — this takes time${RESET}"
  cd $WAVESHARE_DIR/RaspberryPi_JetsonNano/python/
  sudo python3 setup.py install

  # return to home directory
  cd /home/pi
}

function setup_hardware(){
  echo "Setting up SPI"
  if ls /dev/spi* &> /dev/null; then
      echo -e "SPI already enabled"
  else
      if command -v raspi-config > /dev/null && sudo raspi-config nonint get_spi | grep -q "1"; then
          sudo raspi-config nonint do_spi 0
          echo -e "SPI is now enabled"
      else
          echo -e "${RED}There was an error enabling SPI, enable manually with sudo raspi-config${RESET}"
      fi
  fi
}

function install_slowmovie(){
  FIRST_TIME=1  # if this is a first time install

  if [ "$SKIP_DEPS" = false ]; then
    # install from apt
    install_linux_packages

    # configure the hardware
    setup_hardware
  else
    echo -e "Skipping dependency installs, updating SlowMovie code only"
  fi

  if [ -d "${LOCAL_DIR}" ]; then
    echo -e "Existing Install Found - Updating Repo"
    cd $LOCAL_DIR
    git fetch
    git checkout $GIT_BRANCH
    git pull

    # go back to home directory
    cd /home/pi/
  else
    echo -e "No Install Found - Cloning Repo"
    git clone -b ${GIT_BRANCH} ${GIT_REPO} ${LOCAL_DIR}
    FIRST_TIME=0
  fi

  if [ "$SKIP_DEPS" = false ]; then
    # install any needed python packages
    install_python_packages

    # install any additional libraries we need to build manually
    build_python_libraries
  fi

  cd $LOCAL_DIR
  echo -e "SlowMovie install/update complete"

  return $FIRST_TIME
}

function install_service(){
  if [ -d "${LOCAL_DIR}" ]; then
    cd $LOCAL_DIR
    # install the service files and enable
    sudo cp $SERVICE_FILE $SERVICE_DIR
    sudo systemctl daemon-reload
    sudo systemctl enable slowmovie

    echo -e "SlowMovie service installed! Use ${YELLOW}sudo systemctl start slowmovie${RESET} to test"
  else
    echo -e "${RED}SlowMovie repo does not exist! Use option 1 - Install/Upgrade SlowMovie first${RESET}"
  fi

  # go back to home
  cd /home/pi
}

function uninstall_service(){
  if [ -f "${SERVICE_DIR}/${SERVICE_FILE}" ]; then
    # stop if running and remove service files
    sudo systemctl stop slowmovie
    sudo systemctl disable slowmovie
    sudo rm /etc/systemd/system/slowmovie.service
    sudo systemctl daemon-reload

    echo -e "SlowMovie service was successfully uninstalled"
  else
    echo -e "${RED}SlowMovie service is already uninstalled.${RESET}"
  fi
}

# get any options
while getopts ":r:b:si:h" arg; do
    case "${arg}" in
        r)
          GIT_REPO=${OPTARG}
        ;;
        b)
          GIT_BRANCH=${OPTARG}
        ;;
        s)
          SKIP_DEPS=true
        ;;
        h)
          echo "SlowMovie Install/Upgrade Script"
          echo "Use this to install or upgrade your SlowMovie player"
          echo "Advanced Usage:"
          echo "[-r] specify a repo url"
          echo "[-b] specify a repo branch"
          echo "[-s] to skip dependency installs (update SlowMovie code only)"
          exit 0
        ;;
    esac
done

# set the local directory
LOCAL_DIR="/home/pi/$(basename $GIT_REPO)"

cd /home/pi/

INSTALL_OPTION=$(whiptail --menu "\
   _____ _               __  __            _
  / ____| |             |  \/  |          (_)
 | (___ | | _____      _| \  / | _____   ___  ___
  \___ \| |/ _ \ \ /\ / / |\/| |/ _ \ \ / / |/ _ \\
  ____) | | (_) \ V  V /| |  | | (_) \ V /| |  __/
 |_____/|_|\___/ \_/\_/ |_|  |_|\___/ \_/ |_|\___|

 Repo set to '${GIT_REPO}/${GIT_BRANCH}'
 Setting up in local directory '${LOCAL_DIR}'

 Choose what you want to do." 0 0 0 \
1 "Install/Upgrade SlowMovie" \
2 "Install SlowMovie Service" \
3 "Uninstall SlowMovie Service" \
3>&1 1>&2 2>&3)

: ${INSTALL_OPTION:=4}

if [ $INSTALL_OPTION -eq 1 ]; then
	# install or update
  install_slowmovie

  # prompt for service install if the first time being run
  if [ $? -eq 0 ]; then
    whiptail --yesno "SlowMovie install complete. To test, run 'python3 slowmovie.py'\n\nWould you like to install the SlowMovie Service to\nstart playback automatically?" 0 0

    if [ $? -eq 0 ]; then
      install_service
    fi
  fi

elif [ $INSTALL_OPTION -eq 2 ]; then
	# install the service
  install_service
elif [ $INSTALL_OPTION -eq 3 ]; then
	# uninstall the service
  uninstall_service
fi
