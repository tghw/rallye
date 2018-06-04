#!/bin/bash

cd /home/pi/code/rallye
git reset --hard
git pull --rebase origin master
touch /etc/uwsgi-emperor/vassals/rallye.ini
/home/pi/code/rallye/venv/bin/python /home/pi/code/rallye/updater.py restart

