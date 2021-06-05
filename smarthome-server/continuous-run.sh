#!/bin/bash
# You must launch this from the venv in which you installed smarthome

RESULT=`ps -x | grep "smarthome-serve[r]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch"
	smarthome-server >> /tmp/smart-home.log 2>&1 &
else
	echo "Running"
fi
