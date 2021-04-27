#!/bin/bash

cd /home/pi/crespin-control

RESULT=`ps -x | grep "bin/crespi[n]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch"
	/home/pi/crespin-control/bin/crespin >> /tmp/crespin.log 2>&1 &
else
	echo "Running"
fi

