'use strict';

// updates to perform [fct, interval (s), lastUpdateField]
var updates = [
    [setWeather, 10*60, 0],
    [updateBackground, 60, 0],
    [updatePowerPlugStatus, 10, 0],
    [updateRemoteWire, 11, 0],
    [updateNAS, 12, 0],
    [updateMist, 13, 0],
    [displayHourlyWeather, 10*60, 0],
    [updateHue, 29, 0],
    [updateTime, 9, 0],
    [updateRunningSequences, 13, 0]
];

function intervals() {
    for (var i in updates) {
        var el = updates[i];
        if (Date.now() - el[2] > el[1] * 1000) {
            el[2] = Date.now();
            el[0]();
        }
    }
}

function updateTime() {
    var h = new Date().getHours();
    var m = new Date().getMinutes();
    $("#header-time").html((h < 10 ? "0"+h : h) + ":" + (m < 10 ? "0"+m : m));
}

function setWeather() {
    $.get("/api/sensors/weather", function(data) {
        data = data.forecast.simpleforecast.forecastday["0"];
        $("#header-weather-temp-2 span:last").html(data.high.celsius);
        $("#header-weather-temp-2 span:first").html(data.low.celsius);
        $("#header-weather-add-1 span").html(data.pop);
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
        $("#header-weather-icon i").attr("title", data.conditions).tooltip('fixTitle');

        $("#header-weather-add-2 span").html(data.maxwind.kph);
        $("#header-weather-add-2 i").attr("class", "").addClass("wi").addClass("wi-wind")
            .addClass("wi-from-"+data.maxwind.dir.toLowerCase());
        $("#header-weather-add-2 i").attr("title", data.maxwind.dir).tooltip('fixTitle');

        $("#header-day .dayname").html(data.date.weekday.substring(0,3));
        $("#header-day .day").html(data.date.day < 10 ? "0"+data.date.day : data.date.day);
        $("#header-day .month").html(data.date.monthname.substring(0,4));

    });
}

function updateBackground() {
    $("#header-container").css("background-image", "url('/api/sun.svg?"+Date.now()+"')");
}

function updatePowerPlugStatus() {
    $.get('/api/devices/power-plugs', function(data) {
        for (var key in data) {
            var el = $("[data-device='power-plug'][data-id='"+key+"']").find(".toggle");
            if (data[key]["status"] == 1)
                el.addClass("checked");
            else
                el.removeClass("checked");
        }
    });
}

function updateRemoteWire() {
    $.get('/api/devices/remote-pilot-wire', function(data) {
        if (data == "off")
            $("[data-device='remote-pilot-wire'] .toggle3").removeClass("checked-mid").removeClass("checked-right");
        if (data == "eco")
            $("[data-device='remote-pilot-wire'] .toggle3").addClass("checked-mid").removeClass("checked-right");
        if (data == "on")
            $("[data-device='remote-pilot-wire'] .toggle3").removeClass("checked-mid").addClass("checked-right");
    });
}

function updateNAS() {
    $.get('/api/devices/nas', function(data) {
        if (data == "off")
            $("[data-device='nas'] .toggle3").removeClass("checked-mid").removeClass("checked-right");
        else if (data == "on")
            $("[data-device='nas'] .toggle3").removeClass("checked-mid").addClass("checked-right");
        else
            $("[data-device='nas'] .toggle3").addClass("checked-mid").removeClass("checked-right");
    });
}

function updateMist() {
    $.get('/api/devices/mist-lamp', function(data) {
        if (data == true)
            $('[data-device="mist-lamp"] .toggle').addClass("checked");
        else
            $('[data-device="mist-lamp"] .toggle').removeClass("checked");
    });
}

function updateHue() {
    $.get('/hue/lights/1', function (data) {
        if (data.state.on)
            $("#hue_on .toggle").addClass("checked");
        else
            $("#hue_on .toggle").removeClass("checked");

        $("#hue_v").val(data.state.bri);
        var rho = data.state.sat / 255.;
        var phi = data.state.hue / 65535 * 2 * Math.PI - Math.PI;
        var y = rho * Math.cos(phi);
        var x = rho * Math.sin(phi);
        $("#hue_hs_pos").css("left", ((x + 1)*50)+"%");
        $("#hue_hs_pos").css("top", ((y + 1)*50)+"%");
    });
}

function updateRunningSequences() {
        $.get('/api/sensors/threads', function (data) {
        $('#running-seqs .sequence').remove();

        if (Object.keys(data).length > 0)
            $('#running-seqs .text-center').hide();
        else
            $('#running-seqs .text-center').show();

        for (var key in data) {
            var el = $('#running-seqs').append(
                '<p class="sequence '+(data[key]["stop"] ? "stopping": "")+'" data-id="'+key+'">&ndash; '+
                data[key]["title"]+
                ' <i class="fa fa-times-circle-o"></i> <span class="small"><em>Stopping...</em></span></p>');
        }

        $('#running-seqs i').on("click", function () {
            $.ajax('/api/sensors/threads/'+$(this).parent().attr('data-id'), {
                'method': 'PUT'
            });
            $(this).parent().addClass("stopping");
        });
    });
}

function displayHourlyWeather() {
    $.get("/api/sensors/weather/hourly", function (data) {
        $("#header-weather-temp-1 span").html(data.hourly_forecast[0].temp.metric);

        var i, tMin = 50, tMax = -50;
        for (i in data.hourly_forecast) {
            var t = parseInt(data.hourly_forecast[i].temp.metric);
            if (t > tMax) tMax = t;
            if (t < tMin) tMin = t;
        }
        tMax += 2; tMin--;
        if (tMax - tMin < 8) {
            var tmp = tMax + (8 - tMax + tMin) / 2;
            tMin = tMin - (8 - tMax + tMin) / 2;
            tMax = tmp;
        }

        var xScale = 15;
        var yScale = 130 / (tMax - tMin);

        function getY (t) { return (tMax - t) * yScale; }

        var dTemp = "M 0 "+getY(data.hourly_forecast[0].temp.metric);
        var dRain = "M 0 "+(120 - data.hourly_forecast[i].pop);
        var tempTxts = "", rainTxts = "", time = "";
        for (i = 1; i < data.hourly_forecast.length; i++) {
            dTemp += " C " + ((i-0.5)*xScale) + " " + getY(data.hourly_forecast[i-1].temp.metric) +
                     ", "  + ((i-0.5)*xScale) + " " + getY(data.hourly_forecast[i].temp.metric) +
                     ", "  + (i*xScale) + " "+getY(data.hourly_forecast[i].temp.metric);
            dRain += " C " + ((i-0.5)*xScale) + " " + (120 - data.hourly_forecast[i-1].pop) +
                     ", "  + ((i-0.5)*xScale) + " " + (120 - data.hourly_forecast[i].pop) +
                     ", "  + (i*xScale) + " "+ (120 - data.hourly_forecast[i].pop);
            tempTxts += '<text x="'+(i*xScale)+'" y="'+(getY(data.hourly_forecast[i].temp.metric)-3)+'">'+data.hourly_forecast[i].temp.metric+'</text>';
            if (data.hourly_forecast[i].pop > 10)
                rainTxts += '<text x="'+(i*xScale)+'" y="'+(120 - 3 - data.hourly_forecast[i].pop)+'">'+data.hourly_forecast[i].pop+'</text>';
            if (data.hourly_forecast[i].FCTTIME.hour == 0)
                time += '<line class="day" x1="'+(i*xScale)+'" x2="'+(i*xScale)+'" y1="130" y2="0"/><text class="day" x="'+(i*xScale)+'" y="2">'+
                    data.hourly_forecast[i].FCTTIME.weekday_name+' '+data.hourly_forecast[i].FCTTIME.mday+' '+data.hourly_forecast[i].FCTTIME.month_name_abbrev+'</text>';
            else
                time += '<line x1="'+(i*xScale)+'" x2="'+(i*xScale)+'" y1="130" y2="0"/><text x="'+(i*xScale)+'" y="8">'+data.hourly_forecast[i].FCTTIME.hour+'h</text>';

        }

        $("#temperature").attr("d", dTemp);
        $("#precipitation").attr("d", dRain);
        $("#temperature_txts").html(tempTxts);
        $("#precipitation_txts").html(rainTxts);
        $("#weather-time").html(time);
    });
}

/**
 ************ SWITCH TOGGLES **************
 */

function runToggle(el) {
    el = $(el).parents(".command-container");
    var state = el.find(".toggle").hasClass("checked") ? "on" : "off";
    $.ajax(el.attr('data-uri')+'/'+state, {
        'method': 'PUT'
    });
}

function runToggle3(el) {
    el = $(el).parents(".command-container");
    var state = 0;
    if (el.find(".toggle3").hasClass("checked-mid"))
        state = 1;
    if (el.find(".toggle3").hasClass("checked-right"))
        state = 2;
    $.ajax(el.attr('data-uri')+'/'+el.attr('data-values').split(",")[state], {
        'method': 'PUT'
    });
}


$(document).ready(function() {

    // SCENARIOS
    $('#header-content button[data-uri]').click(function () {
        $.ajax($(this).attr('data-uri'), {
            'method': 'PUT'
        });
    });

    // RADIO
    $('#radio button[data-uri]').click(function () {
        $.ajax($(this).attr('data-uri'), {
            'method': 'PUT'
        });
    });

    /**
     ************ SWITCH TOGGLES **************
     */

    $('#switches .toggle').click(function () {
        $(this).toggleClass("checked");
        runToggle(this);
    });

    $('#switches .toggle-container .before').click(function () {
        $(this).parent().find('.toggle').removeClass("checked");
        runToggle(this);
    });

    $('#switches .toggle-container .after').click(function () {
        $(this).parent().find('.toggle').addClass("checked");
        runToggle(this);
    });

    $('#switches .toggle3 .left-btn, #switches .toggle3-container .before').click(function () {
        $(this).parents(".command-container").find('.toggle3').removeClass("checked-mid").removeClass("checked-right");
        runToggle3(this);
    });
    $('#switches .toggle3 .center-btn, #switches .toggle3 .middle:not(.disabled)').click(function () {
        $(this).parents(".command-container").find('.toggle3').addClass("checked-mid").removeClass("checked-right");
        runToggle3(this);
    });
    $('#switches .toggle3 .right-btn, #switches .toggle3-container .after').click(function () {
        $(this).parents(".command-container").find('.toggle3').removeClass("checked-mid").addClass("checked-right");
        runToggle3(this);
    });


    /**
     ************ MIST **************
     */

    $('[data-device="mist-lamp"] button[data-command]').click(function () {
        $.ajax($(this).parents("[data-uri]").data("uri")+"/"+$(this).data("command"), {
            'method': 'PUT'
        });
    });

    /**
     ************ HUE **************
     */


    $("#hue_hs").click(function (e) {
        var x = e.offsetX / $(this).width() * 2 - 1;
        var y = e.offsetY / $(this).height() * 2 - 1;
        var rho = Math.min(Math.sqrt(x*x + y*y), 1);
        var phi = Math.atan2(x, y) + Math.PI;
        var hue_h = phi / Math.PI / 2 * 65535;
        var hue_s = rho * 255;
        $("#hue_hs_pos").css("left", ((rho * Math.sin(phi - Math.PI) + 1)*50)+"%");
        $("#hue_hs_pos").css("top", ((rho * Math.cos(phi - Math.PI) + 1)*50)+"%");
        $.ajax({
            url: '/hue/lights/1/state',
            data : JSON.stringify({"sat": Math.round(hue_s), "hue": Math.round(hue_h)}),
            type: 'PUT'
	    });
    });
    $("#hue_v").change(function () {
        $.ajax({
            url: '/hue/lights/1/state',
            data : JSON.stringify({"bri": Math.round($("#hue_v").val())}),
            type: 'PUT'
	    });
    });

    function hueToggle() {
        $.ajax({
            url: '/hue/lights/1/state',
            data : JSON.stringify({"on": $("#hue_on .toggle").hasClass("checked")}),
            type: 'PUT'
	    });
    }

    $('#hue_on .toggle').click(function () {
        $(this).toggleClass("checked");
        hueToggle();
    });

    $('#hue_on .before').click(function () {
        $(this).parent().find('.toggle').removeClass("checked");
        hueToggle();
    });

    $('#hue_on .after').click(function () {
        $(this).parent().find('.toggle').addClass("checked");
        hueToggle();
    });


    /**
     ************ INTERVALS **************
     */

    setInterval(intervals, 1000);

    $('[data-toggle="tooltip"]').tooltip();
});
