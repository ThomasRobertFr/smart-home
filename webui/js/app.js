'use strict';

const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const dayNamesShort = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const monthNamesShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var pickr = null;

// updates to perform [fct, interval (s), lastUpdateField]
var updates = [
    [setWeather, 10*60, 0],
    //[updateBackground, 60, 0],
    [updatePowerPlugStatus, 10, 0],
    // [updateRemoteWire, 11, 0],
    [updateNAS, 12, 0],
    // [updateCrespinStatus, 35, 0],
    [updateMist, 13, 0],
    [displayHourlyWeather, 10*60, 0],
    [updateHue, 29, 0],
    [updateTime, 9, 0],
    [updateRunningSequences, 13, 0],
    [updateScoll, 5*60, 0],
    [updateCalendar, 10*60, 0]
];

function vibrate() {
    if ("vibrate" in navigator) {
        navigator.vibrate(150);
    }
}

function intervals() {
    for (var i in updates) {
        var el = updates[i];
        if (Date.now() - el[2] > el[1] * 1000) {
            el[2] = Date.now();
            el[0]();
        }
    }
}

function updateScoll() {
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
    $.get("/api/sensors/weather", function(data) {
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
    /* TODO update
    $.get('/api/devices/ir-device/mistlamp', function(data) {
        if (data == true)
            $('[data-device="mist-lamp"] .toggle').addClass("checked");
        else
            $('[data-device="mist-lamp"] .toggle').removeClass("checked");
    });
    */
}

function updateHue() {
    $.get('/hue/lights/1', function (data) {
        var el = $("[data-device='hue-lamp'][data-id='1']").find(".toggle");
        if (data.state.on)
            el.addClass("checked");
        else
            el.removeClass("checked");

        $("#hue_v").val(data.state.bri);
        var rho = data.state.sat / 255.;
        var phi = data.state.hue / 65535 * 2 * Math.PI - Math.PI;
        var y = rho * Math.cos(phi);
        var x = rho * Math.sin(phi);
        $("#hue_hs_pos").css("left", ((x + 1)*50)+"%");
        $("#hue_hs_pos").css("top", ((y + 1)*50)+"%");
    });
}

function updateESPEasyLights() {
    $.get('/api/devices/espeasylights', function (data) {
        // TODO after updating the API to improve it
    });
}

function updateCrespinStatus() {
    $.get('/api/devices/crespin', function(data) {
        if (data == "on")
            $('[data-device="crespin"] .toggle').addClass("checked");
        else
            $('[data-device="crespin"] .toggle').removeClass("checked");
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

    $.get("/api/sensors/weather/hourly", function (data) {
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

/**
 ************ CALENDAR **************
 */

function set_display(calendar_id) {
    $.ajax({
        url: "/calendar/display/calendar/"+calendar_id,
        method: "PUT",
        success: function(data) {
            show_calendar(data);
        }
    });
}

function set_day(calendar_id, year, month, day, state) {
    var day_id = month.toString().padStart(2, 0) + "-" + day.toString().padStart(2, 0);

    $.ajax({
        url: "/calendar/calendars/"+calendar_id+"/"+year+'/'+month+'/'+day+"/"+state,
        type: 'PUT',
        success: function (data) {
            if (state == "on") {
                console.log(day_id);
                $('#calendar_day_'+day_id).addClass("active");
                $('#calendar_day_'+day_id+"_btn").addClass("active");
            }
            else {
                $('#calendar_day_'+day_id).removeClass("active");
                $('#calendar_day_'+day_id+"_btn").removeClass("active");
            }
        }
    });
}

function updateCalendar() {
    $.get("/calendar/calendars", function(data) {
        display_calendar_list(data);
        $.get("/calendar/display", function (display_data) {
            $("#calendar_brightness").val(Math.sqrt(display_data.brightness));
            if (display_data["switch"] == "on")
                $('[data-device="calendar"] .toggle').addClass("checked");
            else
                $('[data-device="calendar"] .toggle').removeClass("checked");
            show_calendar(display_data.calendar);
            calendar_scroll_today();
        });
    });
}

function show_calendar(calendar) {
    $("#calendar_list .btn-group").removeClass("active");
    $('#calendar_list .btn-group[data-id="'+calendar.id+'"]').addClass("active");
    $('#calendar_view .circle').css("background-color", "rgb("+calendar.color+")").removeClass("active").removeClass("active-previously");
    $('#calendar_days .btn').removeClass("active");

    var years = [(parseInt(calendar.current_year) - 1).toString(), calendar.current_year];
    for (var year_i = 0; year_i < years.length; year_i++) {
        var year = years[year_i];
        var months = calendar.days[year];
        for (var i = 0; i < months.length; i++) {
            for (var j = 0; j < months[i].length; j++) {
                if (months[i][j] > 0) {
                    var day = (i + 1).toString().padStart(2, 0) + "-" + (j + 1).toString().padStart(2, 0);
                    if (year == calendar.current_year) {
                        $('#calendar_day_'+day).addClass("active");
                        $('#calendar_day_'+day+"_btn").addClass("active");
                    }
                    else {
                        $('#calendar_day_'+day).addClass("active-previously");
                    }
                }
            }
        }
    }
}

function display_calendar_list(data) {
    var html = "";
    for (var id in data) {
        var active = data[id].active ? "active" : "";
        html += '<div class="btn-group btn-group-xs '+active+'" role="group" style="background-color: rgb('+data[id].color+')" data-id="'+id+'"';
        html += '>';
        html += '<button type="button" class="btn btn-default btn-select">' + data[id].name + '</button>';
        html += '<button type="button" class="btn btn-default btn-edit">';
        html += '<i class="fa fa-pencil"></i>';
        html += '</button></div>';
    }
    html += '<button type="button" class="btn btn-default btn-add btn-xs"><i class="fa fa-plus"></i></button>';
    $("#calendar_list").html(html);

    $("#calendar_list .btn-select").click(function () {
        set_display($(this).parent().data("id"));
    });

    $("#calendar_list .btn-edit").on("click", function () {
        $.get("/calendar/calendars/" + $(this).parent().data("id"), function (data) {
            $("#calendar-name").val(data.name);
            $("#calendar-edit").modal('show');
            $('#calendar-edit form').attr('action', '/calendar/calendars/'+data.id);
            setTimeout(function(){ pickr.setColor('rgb('+ data.color +')'); }, 250);
        });
    });

    $("#calendar_list .btn-add").on("click", function () {
        $("#calendar-edit").modal('show');
        $("#calendar-name").val("");
        $('#calendar-edit form').attr('action', '/calendar/calendars');
        setTimeout(function(){ pickr.setColor('rgb(177, 177, 177)'); }, 250);
    });
}

function calendar_html() {
    var table_html = "<table><tr class='months'><td></td><td>J</td><td>F</td><td>M</td><td>A</td><td>M</td>"
    table_html += "<td>J</td><td>J</td><td>A</td><td>S</td><td>O</td><td>N</td><td>D</td></tr>";
    for (var i = 1; i <= 31; i++) {
        table_html += '<tr><td class="day_title">'+i+'</td>';
        for (var j = 1; j <= 12; j++) {
            var day_id = j.toString().padStart(2, 0) + "-" + i.toString().padStart(2, 0);
            table_html += '<td><span class="circle" id="calendar_day_'+day_id+'"/></td>';
        }
        table_html += "</tr>";
    }
    table_html += "</table>";
    return table_html;
}

function calendar_days_html() {
    // TODO change to show past + coming 1 month. Add a + button for any other day
    var out = '';
    var today = new Date();
    var months = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    for (var i = 1; i <= 12; i++) {
        out += '<div class="month"><div class="title">' + monthNames[i - 1] + '</div>';
        out += '<div class="btn-group btn-group-sm" role="group">';
        for (var j = 1; j <= months[i - 1]; j++) {
            var day_id = i.toString().padStart(2, 0) + "-" + j.toString().padStart(2, 0);
            var cls = "btn btn-default";
            if ((i == today.getMonth() + 1) && (j == today.getDate()))
                cls = "btn btn-primary today";
            out += '<button type="button" class="'+cls+'" data-year="'+today.getFullYear()+'" data-month="'+i+'" data-day="'+j+'" id="calendar_day_'+day_id+'_btn">'+j+'</button>';
        }
        out += '</div></div>';
    }
    return out;
}

function calendar_scroll_today() {
    var delta = $('#calendar_days .today').offset()["left"] - $('#calendar_days').offset()["left"];
    var scroll_val = $('#calendar_days').scrollLeft() + delta;
    scroll_val -= $('#calendar_days').width() / 2;
    scroll_val = Math.max(0, scroll_val);
    $('#calendar_days').scrollLeft(scroll_val);
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
        vibrate();
        $.ajax($(this).attr('data-uri'), {
            'method': 'PUT'
        });
    });

    // RADIO
    $('#radio button[data-uri]').click(function () {
        vibrate();
        $.ajax($(this).attr('data-uri'), {
            'method': 'PUT'
        });
    });

    /**
     ************ SWITCH TOGGLES **************
     */

    $('#switches .toggle').click(function () { vibrate();
        $(this).toggleClass("checked");
        runToggle(this);
    });

    $('#switches .toggle-container .before').click(function () { vibrate(); // "ON" text
        $(this).parent().find('.toggle').removeClass("checked");
        runToggle(this);
    });

    $('#switches .toggle-container .after').click(function () { vibrate(); // "OFF" text
        $(this).parent().find('.toggle').addClass("checked");
        runToggle(this);
    });

    $('#switches .toggle3 .left-btn, #switches .toggle3-container .before').click(function () { vibrate();
        $(this).parents(".command-container").find('.toggle3').removeClass("checked-mid").removeClass("checked-right");
        runToggle3(this);
    });
    $('#switches .toggle3 .center-btn, #switches .toggle3 .middle:not(.disabled)').click(function () { vibrate();
        $(this).parents(".command-container").find('.toggle3').addClass("checked-mid").removeClass("checked-right");
        runToggle3(this);
    });
    $('#switches .toggle3 .right-btn, #switches .toggle3-container .after').click(function () { vibrate();
        $(this).parents(".command-container").find('.toggle3').removeClass("checked-mid").addClass("checked-right");
        runToggle3(this);
    });


    /**
     ************ IR REMOTES BUTTONS **************
     */

    $('[data-device="ir-remote"] button[data-command]').click(function () { vibrate();
        $.ajax($(this).parents("[data-uri]").data("uri")+"/"+$(this).data("command"), {
            'method': 'PUT'
        });
    });

    /**
     ************ ESP EASY DIMMABLE SLIDERS ***********
     */

     $('[data-device="espeasylights"].slider').change(function () { vibrate();
        $.ajax({
            url: $(this).data("uri") + "/" + $(this).val(),
            type: 'PUT'
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

    $('#hue_on .toggle').click(function () { vibrate();
        $(this).toggleClass("checked");
        hueToggle();
    });

    $('#hue_on .before').click(function () { vibrate();
        $(this).parent().find('.toggle').removeClass("checked");
        hueToggle();
    });

    $('#hue_on .after').click(function () { vibrate();
        $(this).parent().find('.toggle').addClass("checked");
        hueToggle();
    });

    /**
     ************ CALENDAR **************
     */

    // html init
    $('#calendar_view').html(calendar_html());
    $('#calendar_days .wrapper').html(calendar_days_html());

    $('#calendar_go_today').click(function () {
        calendar_scroll_today();
    });

    $("#calendar_days .btn").click(function () {
        $(this).toggleClass("active");
        var state = $(this).hasClass("active") ? "on": "off";
        var year = $(this).data("year");
        var month = $(this).data("month");
        var day = $(this).data("day");
        var calendar_id = $("#calendar_list .btn-group.active").data("id");
        set_day(calendar_id, year, month, day, state);
    });

    pickr = Pickr.create({
        el: '#calendar-color-picker',
        theme: 'classic',
        inline: true,
        useAsButton: true,
        lockOpacity: true,
        showAlways: true,
        swatches: [
            'rgb(244, 67, 54)',
            'rgb(233, 30, 99)',
            'rgb(156, 39, 176)',
            'rgb(103, 58, 183)',
            'rgb(63, 81, 181)',
            'rgb(33, 150, 243)',
            'rgb(3, 169, 244)',
            'rgb(0, 188, 212)',
            'rgb(0, 150, 136)',
            'rgb(76, 175, 80)',
            'rgb(139, 195, 74)',
            'rgb(205, 220, 57)',
            'rgb(255, 235, 59)',
            'rgb(255, 193, 7)'
        ],

        components: {
            preview: true,
            opacity: false,
            hue: true,

            interaction: {
                hex: true,
                rgba: true,
                hsva: true,
                input: true,
                clear: false,
                save: false
            }
        }
    });

    $("#calendar-edit-edit").on("click", function () {
        var form = $("#calendar-edit form");
        var color = [];
        var colors_picked = pickr.getColor().toRGBA().slice(0, 3);
        for (var i = 0; i < 3; i++) {
            color.push(Math.round(colors_picked[i]));
        }
        $("#calendar-color").val(""+color)
        $.ajax({
            type: "POST",
            url: form.attr('action'),
            data: form.serialize(),
            success: display_calendar_list
        });
        $("#calendar-edit").modal("hide");
    });

    $("#calendar-edit-delete").on("click", function () {
        var form = $("#calendar-edit form");
        $.ajax({
            type: "DELETE",
            url: form.attr('action'),
            success: function (data) {
                display_calendar_list(data);
                $.get("/calendar/display/calendar", show_calendar);
            }
        });
        $("#calendar-edit").modal("hide");
    });

    $("#calendar_brightness").change(function () {
        $.ajax({
            url: '/calendar/display/brightness/'+Math.round(Math.pow($("#calendar_brightness").val(), 2)),
            type: 'PUT'
	    });
    });

    /**
     ************ CRESPIN **************
     */
    $('#crespin [data-command="run"], #crespin [data-command="pause"], #crespin [data-command="totarget"]').click(function() {
        $.post($('#crespin').data('uri'), {data: $(this).data("command")});
        $('#crespin [data-command="run"], #crespin [data-command="pause"], #crespin [data-command="totarget"]').removeClass("active");
        $(this).addClass("active");
    });

    $('#crespin [data-command="data"]').click(function() {
        $.post($('#crespin').data('uri'), {data: $(this).data("command")}, function (data) {
            $('#crespin [data-command="run"], #crespin [data-command="pause"], #crespin [data-command="totarget"]').removeClass("active");

            data = data.split("\n");

            $('#crespin [data-command="'+data[0]+'"]').addClass("active");
            $('#crespin [data-action="speed-val"]').val(data[1]);

            for (var i = 2; i < data.length; i++) {
                var vals = data[i].split(",");
                $('#crespin [data-motid='+(i-2)+'] .pos').html(vals[0]);
                $('#crespin [data-motid='+(i-2)+'] .target').html(vals[1]);
            }
        });
    });

    function setdata() {
        // full data update (pos & targets) if in position mode
        if ($('#crespin [data-action="position"]').hasClass("active")) {
            var data = "setdata ";
            var n = $('#crespin [data-motid]').length;
            for (var i = 0; i < n; i++) {
                data += $('#crespin [data-motid='+i+'] .pos').html()+" ";
                data += $('#crespin [data-motid='+i+'] .target').html()+" ";
            }
            $.post($('#crespin').data('uri'), {data: data});
        }
        // only target if in normal move mode
        else {
            var data = "settargets ";
            var n = $('#crespin [data-motid]').length;
            for (var i = 0; i < n; i++) {
                data += $('#crespin [data-motid='+i+'] .target').html()+" ";
            }
            $.post($('#crespin').data('uri'), {data: data});
        }
    }
    $('#crespin [data-command="setdata"]').click(function() { setdata(); });

    $('#crespin [data-action="up"], #crespin [data-action="down"]').click(function() {
        var els, delta;
        if ($('#crespin [data-action="target"]').hasClass("active")) {
            els = $('#crespin-motors td.active .target');
            delta = -parseInt($('#crespin [data-action="delta-val"]').val()); // up by default
        }
        else {
            els = $('#crespin-motors td.active .pos');
            delta = parseInt($('#crespin [data-action="delta-val"]').val());
        }
        if ($(this).data("action") == "down")
            delta *= -1;

        els.each(function (i, e) {
            $(e).html(parseInt($(e).html()) + delta);
        });

        if ($('#crespin [data-action="instant"]').hasClass("active") && !$('#crespin [data-action="instant"]').hasClass("disabled")) {
            setdata();
        }
    });

    $('#crespin [data-action="setpos"], #crespin [data-action="settarget"]').click(function() {
        var field = $(this).data("action") == "setpos" ? "pos" : "target";
        var els = $('#crespin-motors td.active .'+field);
        var val = parseInt($(this).parent().parent().find("input").val());
        els.each(function (i, e) { $(e).html(val); });

        if ($('#crespin [data-action="instant"]').hasClass("active") && !$('#crespin [data-action="instant"]').hasClass("disabled")) {
            setdata();
        }
    });

    $('#crespin [data-action="setspeed"]').click(function() {
        var val = parseInt($(this).parent().parent().find("input").val());
        $.post($('#crespin').data('uri'), {data: "setspeed "+val});
    });

    $('#crespin [data-action="target"], #crespin [data-action="position"]').click(function() {
        $('#crespin [data-action="target"], #crespin [data-action="position"]').removeClass("active");
        $(this).addClass("active");
        if ($(this).data("action") == "position")
            $('#crespin [data-action="instant"]').addClass("disabled");
        else
            $('#crespin [data-action="instant"]').removeClass("disabled");
    });

    $('#crespin [data-action="multiselect"], #crespin [data-action="instant"]').click(function() {
        $(this).toggleClass("active");
    });

    $('#crespin [data-action="selectall"]').click(function() {
        if ($('#crespin-motors td.active').length > 0)
            $('#crespin-motors td').removeClass('active');
        else
            $('#crespin-motors td').addClass('active');
    });

    $('#crespin-motors td').click(function() {
        if ($('#crespin [data-action="multiselect"]').hasClass("active")) {
            $(this).toggleClass("active");
        }
        else {
            var activeBefore = $(this).hasClass("active");
            $('#crespin-motors td').removeClass("active");
            if (!activeBefore)
                $(this).addClass("active");
        }
    });


    /**
     ************ INTERVALS **************
     */

    setInterval(intervals, 1000);

    $('[data-toggle="tooltip"]').tooltip({container: 'body'});
});
