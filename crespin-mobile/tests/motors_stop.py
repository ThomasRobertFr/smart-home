import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

data = 17
out = 27
shift = 22

GPIO.setup(data, GPIO.OUT)
GPIO.setup(out, GPIO.OUT)
GPIO.setup(shift, GPIO.OUT)

GPIO.output(shift, GPIO.LOW)
GPIO.output(out, GPIO.LOW)


Seq = range(0, 8)
Seq[0] = [0,1,0,0]
Seq[1] = [0,1,0,1]
Seq[2] = [0,0,0,1]
Seq[3] = [1,0,0,1]
Seq[4] = [1,0,0,0]
Seq[5] = [1,0,1,0]
Seq[6] = [0,0,1,0]
Seq[7] = [0,1,1,0]

# seq   rose orange bleu jaune
# write last              first
# real: bleu rose jaune orange


def put(val):
    GPIO.output(data, GPIO.HIGH if val else GPIO.LOW)
    GPIO.output(shift, GPIO.HIGH)
    GPIO.output(shift, GPIO.LOW)

def output():
    GPIO.output(out, GPIO.HIGH)
    GPIO.output(out, GPIO.LOW)

def putSeq(i):
    out = Seq[i]
    put(out[1])
    put(out[3])
    put(out[0])
    put(out[2])

# Shutdown motors
#
for motI in range(8):
    for pins in range(4):
        put(0)
output()
