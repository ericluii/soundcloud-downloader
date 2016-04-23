#!/bin/bash

echo 'Checking if pip exists.'
pip > /dev/null
rc=$?

if [[ $rc != 0 ]]; then
  echo 'Installing pip...'
  curl -# -o get-pip.py https://bootstrap.pypa.io/get-pip.py
  sudo python get-pip.py
  rm get-pip.py
else
  echo 'Pip detected. Skipping Install.'
fi

echo '========================================='
echo 'Installing Dependencies:'
echo '- eyeD3'
echo '========================================='

sudo pip install eyed3

echo '========================================='
echo 'Good to go (:'
