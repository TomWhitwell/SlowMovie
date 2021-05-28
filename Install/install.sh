#!/bin/bash -e

GIT_REPO=https://github.com/TomWhitwell/SlowMovie
GIT_BRANCH=main
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

function service_installed(){
  # return 0 if the service is installed, 1 if no
  if [ -f "$SERVICE_DIR/$SERVICE_FILE" ]; then
    return 0
  else
    return 1
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

  # generate a default config file if missing
  if [ ! -f "${LOCAL_DIR}/slowmovie.conf" ]; then
    cp "${LOCAL_DIR}/Install/slowmovie-default.conf" "${LOCAL_DIR}/slowmovie.conf"
  fi

  if [ "$SKIP_DEPS" = false ]; then
    # install any needed python packages
    install_python_packages

  fi

  cd $LOCAL_DIR

  # check if the service file needs to be updated
  if (service_installed) && ! (cmp -s "slowmovie.service" "/etc/systemd/system/slowmovie.service"); then
    sudo cp $SERVICE_FILE $SERVICE_DIR
    sudo systemctl daemon-reload

    echo -e "Updating SlowMovie service file"
  fi

  echo -e "SlowMovie install/update complete. To test, run '${YELLOW}python3 ${LOCAL_DIR}/slowmovie.py${RESET}'"

  return $FIRST_TIME
}

function install_service(){
  if [ -d "${LOCAL_DIR}" ]; then
    cd $LOCAL_DIR

    if ! (service_installed); then
      # install the service files and enable
      sudo cp $SERVICE_FILE $SERVICE_DIR
      sudo systemctl daemon-reload
      sudo systemctl enable slowmovie

      echo -e "SlowMovie service installed! Use ${YELLOW}sudo systemctl start slowmovie${RESET} to test"
    else
      echo -e "${RED}SlowMovie service is already installed.${RESET}"
    fi
  else
    echo -e "${RED}SlowMovie repo does not exist! Use option 1 - Install/Upgrade SlowMovie first${RESET}"
  fi

  # go back to home
  cd /home/pi
}

function uninstall_service(){
  if (service_installed); then
    # stop if running and remove service files
    sudo systemctl stop slowmovie
    sudo systemctl disable slowmovie
    sudo rm "${SERVICE_DIR}/${SERVICE_FILE}"
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

# check if service is currently running and stop if it is
RESTART_SERVICE="FALSE"

if (systemctl is-active --quiet slowmovie); then
  sudo systemctl stop slowmovie
  RESTART_SERVICE="TRUE"
fi

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

  # prompt for service install if the first time being run (whiptail 1=No)
  INSTALL_SERVICE=1
  if [ ! -d "${LOCAL_DIR}" ]; then
    whiptail --yesno "Would you like to install the SlowMovie Service to\nstart playback automatically?" 0 0
    INSTALL_SERVICE=$?
  fi

	# install or update
  install_slowmovie

  # install service, if desired
  if [ $INSTALL_SERVICE -eq 0 ]; then
    install_service
  fi

elif [ $INSTALL_OPTION -eq 2 ]; then
	# install the service
  install_service
elif [ $INSTALL_OPTION -eq 3 ]; then
	# uninstall the service
  uninstall_service
fi

if [ "${RESTART_SERVICE}" = "TRUE" ] && (service_installed); then
  sudo systemctl start slowmovie
fi
