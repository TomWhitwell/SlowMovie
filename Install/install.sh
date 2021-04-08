#!/bin/bash -e

GIT_REPO=https://github.com/TomWhitwell/SlowMovie
GIT_BRANCH=master
PYTHON_VERSION=3
SKIP_DEPS=false

function install_linux_packages(){
  sudo apt-get update

  sudo apt-get install -y ffmpeg git python3-pip
}

function install_python_packages(){
  # set the python3 as the default version
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
  sudo update-alternatives --set python /usr/bin/python${PYTHON_VERSION}


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

  echo -e "$(tput setaf 1)Be patient - this takes time$(tput sgr 0)"
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
          echo -e "$(tput setaf 1)There was an error enabling SPI, enable manually with sudo raspi-config$(tput sgr 0)"
      fi
  fi
}

function install_slowmovie(){
  if [ "$SKIP_DEPS" = false ]; then
    # install from apt
    install_linux_packages

    # configure the hardware
    setup_hardware
  else
    echo -e "Skipping dependency installs, updating SlowMovie code only"
  fi

  if [ -d "${LOCAL_DIR}" ]; then
    echo -e "Existing Install - Updating Repo"
  else
    echo -e "No Install Found - Cloning Repo"
    git clone ${GIT_REPO} ${LOCAL_DIR}
  fi

  # update the repo
  cd $LOCAL_DIR
  git fetch
  git checkout $GIT_BRANCH
  git pull

  # go back to home directory
  cd /home/pi/

  if [ "$SKIP_DEPS" = false ]; then
    # install any needed python packages
    install_python_packages

    # install any additional libraries we need to build manually
    build_python_libraries
  fi

  cd $LOCAL_DIR
  echo -e "SlowMovie install complete"
  echo -e "To test run $(tput setaf 3)python3 slowmovie.py$(tput sgr 0)"

}

function install_service(){
  if [ -d "${LOCAL_DIR}" ]; then
    cd $LOCAL_DIR
    # install the service files and enable
    sudo cp slowmovie.service /etc/systemd/system
    sudo systemctl daemon-reload
    sudo systemctl enable slowmovie

    echo -e "SlowMovie service installed use $(tput setaf 3)sudo systemctl start slowmovie$(tput sgr 0) to test"
  else
    echo -e "$(tput setaf 1)SlowMovie repo does not exist, do that first$(tput sgr 0)"
  fi

  # go back to home
  cd /home/pi
}

function uninstall_service(){
  if [ -f "/etc/systemd/system/slowmovie.service" ]; then
    # stop if running and remove service files
    sudo systemctl stop slowmovie
    sudo systemctl disable slowmovie
    sudo rm /etc/systemd/system/slowmovie.service
    sudo systemctl daemon-reload

    echo -e "SlowMovie service is uninstalled"
  else
    echo -e "$(tput setaf 1)SlowMovie is not installed, nothing to clean up$(tput sgr 0)"
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

# clear screen
  clear;

  # Set color of logo
  # Logo generated from: http://patorjk.com/software/taag/
  tput setaf 4
  tput bold

  cat << "EOF"
     _____ _               __  __            _
    / ____| |             |  \/  |          (_)
   | (___ | | _____      _| \  / | _____   ___  ___
    \___ \| |/ _ \ \ /\ / / |\/| |/ _ \ \ / / |/ _ \
    ____) | | (_) \ V  V /| |  | | (_) \ V /| |  __/
   |_____/|_|\___/ \_/\_/ |_|  |_|\___/ \_/ |_|\___|

EOF

# reset terminal color
tput sgr 0

echo -e "SlowMovie Repo set to $(tput setaf 3)${GIT_REPO}/${GIT_BRANCH}$(tput sgr 0)"
echo -e "Setting up in local directory $(tput setaf 3)${LOCAL_DIR}$(tput sgr 0)"
echo -e ""
cd /home/pi/

echo "1 - Install/Upgrade SlowMovie"
echo "2 - Install SlowMovie Service"
echo "3 - Uninstall SlowMovie Service"
echo "4 - Exit"
echo ""

INSTALL_OPTION=0

while [ "$INSTALL_OPTION" = "" ] || [ $INSTALL_OPTION -le 0 ] || [ $INSTALL_OPTION -gt 4 ]; do
        read -p "Choose what you want to do? " INSTALL_OPTION
done

if [ $INSTALL_OPTION -eq 1 ]; then
	# install or update
  install_slowmovie
elif [ $INSTALL_OPTION -eq 2 ]; then
	# install the service
  install_service
elif [ $INSTALL_OPTION -eq 3 ]; then
	# uninstall the service
  uninstall_service
fi
