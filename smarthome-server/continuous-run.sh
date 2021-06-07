#!/bin/bash
# You must launch this from the venv in which you installed smarthome

RESULT=`ps -x | grep "smarthome-serve[r]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch Smarthome Server"
	smarthome-server >> /tmp/smart-home.log 2>&1 &
else
	echo "Running Smarthome Server"
fi

RESULT=`ps -x | grep "celery -A smarthome.celer[y]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch Celery"
	celery -A smarthome.celery worker --loglevel=INFO >> /tmp/smart-home-celery.log 2>&1 &
else
	echo "Running Celery"
fi
