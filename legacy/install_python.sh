#!/usr/bin/env bash

################
# Python 3.7.4 #
################

# First install the dependencies needed to build
sudo apt-get update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev

# Compile (takes a while!)
wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tar.xz
tar xf Python-3.7.4.tar.xz
cd Python-3.7.4
./configure --prefix=/usr/local/opt/python-3.7.4
make -j 4

# install
sudo make altinstall

# Make Python 3.7.4 the default version, make aliases
sudo ln -s -f /usr/local/opt/python-3.7.4/bin/pydoc3.7 /usr/bin/pydoc3.7
sudo ln -s -f /usr/local/opt/python-3.7.4/bin/python3.7 /usr/bin/python3.7
sudo ln -s -f /usr/local/opt/python-3.7.4/bin/python3.7m /usr/bin/python3.7m
sudo ln -s -f /usr/local/opt/python-3.7.4/bin/pyvenv-3.7 /usr/bin/pyvenv-3.7
sudo ln -s -f /usr/local/opt/python-3.7.4/bin/pip3.7 /usr/bin/pip3.7
alias python3='/usr/bin/python3.7'
alias pip3='/usr/bin/pip3.7'
ls /usr/bin/python*
cd ..
sudo rm -r Python-3.7.4
rm Python-3.7.4.tar.xz
. ~/.bashrc
