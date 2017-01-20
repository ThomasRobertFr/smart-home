# Smart home server

This repository contains the code for the my small and personal smart-home project.

# TODOs

* Display home state
* Scenarios options handling (python + ui)
    * Early wake up option
* Improve scenarios:
    * Heating based on inside and outside temp
    * Lights based on sun altitude
    * Add movie scenario?
* Add auto triggers:
    * light on based on home state + sunset
    * heating based on home state + temperatures
* Schedule events in calendar
* Better radio widget
* Voice recognition
* Velib status

# Hardware

* **Server:** Raspberry Pi
* **Devices:**
    * Philips Hue bride
    * Philips Hue color lamp bulb
    * 8 Etekcity RF-controlled power-plug adapters
    * Speakers + jack
    * NAS + wire soldered on the power-on switch
* **Electronics:**
    * 5V to 3.3V adapter
    * RF 433 MHz transmitter & receiver
    * Temperature sensor (DHT11)
    * Motion sensor (PIR)

# Software

## Packages

```
# apt-get

## Basics
zsh python-pip git tig htop

## Routing & web
dnsmasq nginx php5-fpm

## Python
python python-pip python3 python3-pip

## Text-to-speech
lame alsa-mixer libttspico-utils sox

# pip
google-api-python-client requests pytz python-dateutil
```

## dnsmask setup

To be able to give hostnames to our local IPs, we will use the raspi as a DNS server using `dnsmask`.

This config file in `/etc/dnsmask.conf` will serve the domains in `/etc/hosts`:

```
domain-needed # Don't forward bogus request to the real DNS
bogus-priv # Don't forward bogus request to the real DNS
no-resolv # Don't look at resolv.conf
server=192.168.1.254 # Default DNS
local=/local/ # Pattern for local domains
```

**Auto-startup:** `sudo systemctl enable dnsmasq`

## Mopidy (MPD music server with Google Music)

```
wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list
sudo apt-get install mopidy
sudo pip install mopidy-gmusic
```

## Web server

`sudo /etc/init.d/nginx start`

Comfiguration in `sites-enabled/default`:

```
server {
    
    # [...]
    
    # Enable PHP index
    index index.html index.php;

	server_name _;

    # Allow access from local IP without password, outside with password
    # Please create the /etc/nginx/htpasswd/default.htpasswd file
	satisfy any;
	allow 192.168.0.0/16;
	allow 127.0.0.1/32;
	deny all;
	auth_basic "Home";
	auth_basic_user_file /etc/nginx/htpasswd/default.htpasswd;

    # Redirect API calls
	location ~ ^/api/(.*)$ {
		proxy_pass http://<API_URL>/$1$is_args$args;
	}

    # Redirect HUE calls
	location ~ ^/hue/(.*)$ {
		proxy_pass http://<HUE_URL>/api/<HUE_USERNAME>/$1$is_args$args;
	}

    # Regular files are served
	location / {
		try_files $uri $uri/ =404;
	}

	# Handle PHP
	location ~ \.php$ {
		include snippets/fastcgi-php.conf;
		fastcgi_pass unix:/var/run/php5-fpm.sock;
	}
}
```

## Smart-home crons

```
* * * * *    cd /home/pi/dev/smart-home && ./continuous-run.sh
*/10 * * * * curl -X GET http://<API_URL>/triggers/calendar/update
* * * * *    curl -X GET http://<API_URL>/triggers/calendar/trigger
```