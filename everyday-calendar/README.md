# Smart calendar

This project is inspired by [Simone Giertz's Everyday Calendar](https://www.simonegiertz.com/every-day-calendar).
This is my take on this with a much lower budget and slightly different features.

This calendar is built with:

* A poster frame with glass window
* A paper printed calendar with all days in a year
* A thin MDF board with 365 holes aligned with the calendar
* An RGB indexable LED ribbon with 1 LED in each hole of the board
* A Raspberry Pi Zero W to control the LEDs

The Raspberry Pi will need to run the server code in this folder. This code will
expose routes to interract with the calendar:

* tick/untick a day
* set the currently viewed calendar
* set the brightness of the calendar

To interract with this calendar, I personnaly use the front UI of the
[smarthome-server](../smarthome-server/README.md) project which includes interractions
with this server. This UI is always directly on an old smartphone in my living room.

Compared to Simone's calendar, you cannot physically interract with the calendar,
you need to call the API somehow. However, you can have multiple calendars each with a
different color.

### Some photos of the build

MDF board with holes, work in progress

![](MDF_board.jpg)

MDF board finished, LED ribbon installed and being tested

![](POC_MDF_and_LEDs.jpg)

Final calendar

![](Calendar.jpg)

### Ideas for the future

* Show multiple calendars at once
* Iterate on the different calendars each _X_ minutes
* Connect to Google Calendar to show your real calendar visually


## Install on the raspberry pi

**Install Python 3.7**

```
# Build python 3.7 if needed
sudo apt-get update -y
sudo apt-get install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev -y

wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tar.xz
tar xf Python-3.7.4.tar.xz
cd Python-3.7.4
./configure
make -j 4
sudo make altinstall

# install poetry
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3.7 -
```

**Deploy / configure**

```
scp -r ../everyday-calendar pi@192.168.1.20:dev
ssh pi@192.168.1.20

# First setup create venv
python3.7 -m venv venv
source venv/bin/activate
~/.poetry/bin/poetry install

# To run
everyday-calendar
```

**In crontab of root user**

```
* * * * *    cd /home/pi/dev/everyday-calendar && . venv/bin/activate && ./continuous-run.sh > /dev/null 2>&1
*/5 * * * *  curl http://localhost:5000/save >/dev/null 2>&1
```
