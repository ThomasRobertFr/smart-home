#!/bin/bash

RESULT=`ps -x | grep "run.p[y]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch"
	/home/pi/dev/smart-home/run.py >> /tmp/smart-home.log 2>&1 &
else
	echo "Running"
fi

RESULT=`ps -x | grep "smarthome.triggers._RFComman[d]"`

if [ "${RESULT:-null}" = null ]; then
        echo "Launch RF"
	python3 -m smarthome.triggers._RFCommand >> /tmp/smart-home-rf.log 2>&1 &
else
	echo "Running RF"
fi

RESULT=`ps -x | grep "google-home.google-hom[e]"`

if [ "${RESULT:-null}" = null ]; then
        echo "Launch Google Home"
	/home/pi/ghomeenv/bin/python -m google-home.google-home >> /tmp/google-home.log 2>&1 &
else
	echo "Running Google Home"
fi
