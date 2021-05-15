#!/bin/bash

RESULT=`ps -x | grep "smarthome.api:ap[p]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch"
	source /home/pi/dev/smart-home/.venv/bin/activate; /home/pi/dev/smart-home/run.sh >> /tmp/smart-home.log 2>&1 &
else
	echo "Running"
fi

#RESULT=`ps -x | grep "smarthome.triggers._RFComman[d]"`
#
#if [ "${RESULT:-null}" = null ]; then
#        echo "Launch RF"
#	python3 -m smarthome.triggers._RFCommand >> /tmp/smart-home-rf.log 2>&1 &
#else
#	echo "Running RF"
#fi
#
#RESULT=`ps -x | grep "google-home.google-hom[e]"`
#
#if [ "${RESULT:-null}" = null ]; then
#        echo "Launch Google Home"
#	/home/pi/ghomeenv/bin/python -m google-home.google-home >> /tmp/google-home.log 2>&1 &
#else
#	echo "Running Google Home"
#fi
