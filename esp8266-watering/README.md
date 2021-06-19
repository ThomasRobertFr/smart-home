# Homemade watering system

The goal of this project is to be able to automatically water small plant pots
from a standing water reserve (i.e. without a pressured water tap) and without
a mains power supply.

One device can measure the moisture and water up to 3 pots.

For this, I use:

* an ESP8266 chip for control and wifi communication to get watering rules (cf
  `smarthome-server/smarthome/watering`)
* a pack of batteries (initially 4x1.2V NiMH batteries, now 2x4.2V li-ion batteries)
* an [HT7833 voltage regulator](HT78xx.pdf) to very efficiently (~4mA loss) power the
  ESP with a 3.3V source. An [HT7333](HT73xx.pdf) can also be used but has less max
  power output which might be a problem with ESP8266. In practice, it seems to work.
* soil moisture sensors in parallel all plugged into the analog read of the ESP, with
  only one powered (from ESP output pin) at any time to be able to read all of them.
* small water pumps powered directly from the battery pack and controlled by ESP
  output pins with a 2N2222 transistor.

In the `src` folder you will find the code that is used to program the ESP8266.
It needs to be able to call the watering API of the `smarthome-server` project.

### Schematics and real build

The schematics of this project is quite simple:

![](schematics.png)

All this is build with a PCB-like board soldered on the right side of the
NodeMCU ESP8266 dev board following this compact and wierd design:

![](pcb_schematics.png)

In real life, the PCB looks like this:

![](pcb_real.jpg)

And the device put in place:

![](watering_real.jpg)

