#!/bin/bash

touch /etc/uwsgi-emperor/vassals/rallye.ini
/home/pi/code/rallye/venv/bin/python /home/pi/code/rallye/updater.py restart

