pid=`ps ax | grep "smarthome-serve[r]" | sed 's/\([0-9]\+\)\s.\+$/\1/'`
echo $pid
kill $pid
while kill -9 $pid 2> /dev/null; do sleep 0.5; done

pid=`ps ax | grep "celery -A smarthome.sequence[s]" | sed 's/\([0-9]\+\)\s.\+$/\1/'`
echo $pid
kill $pid
while kill -0 $pid 2> /dev/null; do sleep 0.5; done
