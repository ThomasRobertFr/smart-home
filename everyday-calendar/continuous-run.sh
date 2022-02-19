#!/bin/bash
# You must launch this from the venv in which you installed everyday-calendar, as root

RESULT=`ps -x | grep "everyday-calenda[r]"`

if [ "${RESULT:-null}" = null ]; then
	echo "Launch"
	everyday-calendar >> /tmp/calendar.log 2>&1 &
else
	echo "Running"
fi
