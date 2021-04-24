'use strict';

// register updates to perform [fct, interval (s), lastUpdateField]
updates = updates.concat([
    [setWeather, 10*60, 0],
    [displayHourlyWeather, 10*60, 0],
    [updateTime, 9, 0],
    [updateScroll, 5*60, 0],
    [updateBackground, 10*60, 0]
]);

function updateScroll() {
    var h = new Date().getHours();
    var m = new Date().getMinutes();

    var timeFloat = Math.max(0, h + m / 60 - 3.5) * 600;

    $("header").scrollLeft(timeFloat);
}

function updateTime() {
    var h = new Date().getHours();
    var m = new Date().getMinutes();
    $("#header-time").html((h < 10 ? "0"+h : h) + ":" + (m < 10 ? "0"+m : m));
}

function setWeather() {
    $.get(baseURL + "/api/sensors/weather", function(data) {
        data = data.daily.data[0];
        $("#header-weather-temp-2 span:last").html(Math.round(data.temperatureHigh));
        $("#header-weather-temp-2 span:first").html(Math.round(data.temperatureLow));
        $("#header-weather-add-1 span").html(Math.round(data.precipProbability*100));
        var icons = {
            "clear": "wi-day-sunny",
            "cloudy": "wi-cloud",
            "flurries": "wi-snow",
            "fog": "wi-fog",
            "hazy": "wi-day-haze",
            "sleet": "wi-sleet",
            "rain": "wi-rain",
            "snow": "wi-snowflake-cold",
            "sunny": "wi-day-sunny",
            "tstorms": "wi-thunderstorm",
            "chanceflurries": "wi-snow",
            "chancerain": "wi-showers",
            "chancesleet": "wi-sleet",
            "chancesnow": "wi-snow",
            "chancetstorms": "wi-storm-showers",
            "partlysunny": "wi-day-sunny-overcast",
            "partlycloudy": "wi-day-cloudy",
            "mostlycloudy": "wi-day-cloudy",
            "mostlysunny": "wi-day-sunny-overcast"
        };
        $("#header-weather-icon i").attr("class", "").addClass("wi").addClass(icons[data.icon] || "wi-na");
        $("#header-weather-icon i").attr("title", data.summary).tooltip('fixTitle');

        $("#header-weather-add-2 span").html(Math.round(data.windGust));
        $("#header-weather-add-2 i").attr("class", "").addClass("wi").addClass("wi-wind")
            .addClass("from-"+Math.round(data.windBearing)+"-deg");
        //$("#header-weather-add-2 i").attr("title", Math.round(data.windBearing)+"").tooltip('fixTitle');

        var d = new Date();
        $("#header-day .dayname").html(dayNamesShort[d.getDay()]);
        $("#header-day .day").html(d.getDate() < 10 ? "0"+d.getDate() : d.getDate());
        $("#header-day .month").html(monthNamesShort[d.getMonth()]);

    });
}

function updateBackground() {
    $("#header-container").css("background-image", "url('" + baseURL + "/api/sun.svg?"+Date.now()+"')");
}

function displayHourlyWeather() {
    var icons = {
        "clear": "f00d", // "wi-day-sunny",
        "clear-day": "f00d", // "wi-day-sunny",
        "clear-night": "f02e", // "wi-night-clear"
        "cloudy": "f041", // "wi-cloud",
        "flurries": "f01b", //"wi-snow",
        "fog": "f014", // "wi-fog",
        "hazy": "f0b6", // "wi-day-haze",
        "sleet": "f0b5", //"wi-sleet",
        "rain": "f019", //"wi-rain",
        "snow": "f076", //"wi-snowflake-cold",
        "wind": "f085", // wi-day-windy
        "sunny": "f00d", // "wi-day-sunny",
        "tstorms":"f01e", // "wi-thunderstorm",
        "chanceflurries": "f01b", //"wi-snow",
        "chancerain": "f01a", // "wi-showers",
        "chancesleet": "f0b5", //"wi-sleet",
        "chancesnow": "f01b", //"wi-snow",
        "chancetstorms": "f01d", //"wi-storm-showers",
        "partlysunny": "f00c", // "wi-day-sunny-overcast",
        "partly-cloudy-day": "f002", //"wi-day-cloudy",
        "partly-cloudy-night": "f031", //"wi-night-cloudy",
        "partlycloudy": "f002", //"wi-day-cloudy",
        "mostlycloudy": "f002", //"wi-day-cloudy",
        "mostlysunny": "f00c" // "wi-day-sunny-overcast"
    };

    $.get(baseURL + "/api/sensors/weather/hourly", function (data) {
        $("#header-weather-temp-1 span").html(Math.round(data.currently.temperature));

        data = data.hourly.data

        var i, tMin = 50, tMax = -50;
        for (i in data) {
            var t = Math.round(data[i].temperature);
            if (t > tMax) tMax = t;
            if (t < tMin) tMin = t;
        }
        //tMax += 2; tMin--;
        if (tMax - tMin < 8) {
            var tmp = tMax + (8 - tMax + tMin) / 2;
            tMin = tMin - (8 - tMax + tMin) / 2;
            tMax = tmp;
        }

        var dx = 15;
        var dy = 83 / (tMax - tMin);

        function getTemp(i) { return Math.round(data[i].temperature); }
        function getYTemp(i) { return (tMax - Math.round(data[i].temperature)) * dy + 38; }
        function getRain(i) { return Math.round(data[i].precipProbability * 100); }
        function getYRain(i) { return 120 - Math.round(data[i].precipProbability * 100); }

        var dTemp = "M 0 "+getYTemp(0);
        var dRain = "M 0 "+getYRain(0);
        var tempTxts = "", rainTxts = "", time = "";
        for (i = 1; i < data.length - 1; i++) {
            var dateI = (new Date(data[i].time*1000));

            dTemp += " S " + ((i-0.3333)*dx) + " " + (getYTemp(i) - (getYTemp(i+1) - getYTemp(i-1)) / 6) +
                     ", "  + (i*dx) + " "+getYTemp(i);

            dRain += " S " + ((i-0.3333)*dx) + " " + (getYRain(i) - (getYRain(i+1) - getYRain(i-1)) / 6) +
                     ", "  + (i*dx) + " "+ getYRain(i);

            tempTxts += '<text x="'+(i*dx)+'" y="'+(getYTemp(i)-3)+'">'+getTemp(i)+'</text>';
            if (getRain(i) > 10)
                rainTxts += '<text x="'+(i*dx)+'" y="'+(120 - 3 - getRain(i))+'">'+getRain(i)+'</text>';
            if (dateI.getHours() == 0)
                time += '<line class="day" x1="'+(i*dx)+'" x2="'+(i*dx)+'" y1="130" y2="0"/><text class="day" x="'+(i*dx)+'" y="2">'+
                    dayNames[dateI.getDay()]+' '+dateI.getDate()+' '+monthNames[dateI.getMonth()]+'</text>';
            else
                time += '<line x1="'+(i*dx)+'" x2="'+(i*dx)+'" y1="130" y2="0"/>' +
                        '<text x="'+(i*dx)+'" y="8">'+dateI.getHours()+'h</text>' +
                            '<text class="weather weather-'+data[i].icon+'" x="'+(i*dx)+'" y="23">&#x'+icons[data[i].icon]+'</text>';

        }

        $("#temperature").attr("d", dTemp);
        $("#precipitation").attr("d", dRain);
        $("#temperature_txts").html(tempTxts);
        $("#precipitation_txts").html(rainTxts);
        $("#weather-time").html(time);
    });
}
