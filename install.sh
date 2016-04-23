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

eyed3 > /dev/null
rc=$?

if [[ $rc != 0 ]]; then
  sudo pip install eyed3
else
  echo 'eyed3 detected. Skipping Install.'
fi

echo '========================================='
echo 'Good to go (:'
