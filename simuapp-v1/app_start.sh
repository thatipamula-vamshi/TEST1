#!/bin/bash
echo Starting application server [Run this as sudo su]

# nohup (No Hang Up) is a command in Linux systems that runs the process even after logging out from the shell/terminal
# ">> application.log" pushes all your stdout in the log file
# "2>&1" pushes all the stderr to the log file (This would push all the error logs to the log file as well)
# "&" at the end makes it run in the background.
cd /opt
nohup python3 simu_app.py >> application.log 2>&1 &

echo Listing the application process
ps -ef | grep [s]imu_app

echo Done
