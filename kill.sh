pid=`ps ax | grep "smarthome.server:ap[p]" | sed 's/\([0-9]\+\)\s.\+$/\1/'`
echo $pid
kill $pid
while kill -0 $pid 2> /dev/null; do sleep 0.5; done

#pid=`ps ax | grep 'smarthome.triggers._RFComman[d]' | sed 's/\([0-9]\+\)\s.\+$/\1/'`
#echo $pid
#kill $pid
#while kill -0 $pid 2> /dev/null; do sleep 0.5; done
#
#pid=`ps ax | grep 'google-home.google-hom[e]' | sed 's/\([0-9]\+\)\s.\+$/\1/'`
#echo $pid
#kill $pid
#while kill -0 $pid 2> /dev/null; do sleep 0.5; done
