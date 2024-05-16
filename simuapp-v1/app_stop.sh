#!/bin/bash

echo Listing the application processes
ps -ef | grep [s]imu_app

echo Killing the application processes now
sudo kill -9 $(ps -ef | grep [s]imu_app | awk '{printf "%s ", $2}')

echo Listing the application processes again, this should be empty
ps -ef | grep [s]imu_app

echo Done
