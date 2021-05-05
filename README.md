# Smart home server

This repository contains the code for the my small and personal smart-home project.

The folders are:

* `smarthome-server`: main folder with the code of the server that handles the smart-home project
* `everyday-calendar`: code for the small server that handles my version of the Everyday Calendar
* `esp8266-ac-dimmer`: code for the ESP8266 that handles the dimming of an 230V LED bulb from IKEA
   based on a [Robodyn Dimmer](https://github.com/RobotDynOfficial/RBDDimmer)
* `esp8266-watering`: code for ESP8266 handling watering of my plants

### Dev notes

Code should be YAPF'ified and isort'ed. A pre-commit hook should be installed
to ensure it, using :

```bash
find .git/hooks -type l -exec rm {} \;
find .githooks -type f -exec ln -sf ../../{} .git/hooks/ \;
```

Install pre-commit 
