'use strict';

var pickr = null;

// updates to perform [fct, interval (s), lastUpdateField]
updates = updates.concat([
    [updateCalendar, 10*60, 0]
]);

function set_display(calendar_id) {
    $.ajax({
        url: calendarURL + "display/calendar/"+calendar_id,
        method: "PUT",
        success: function(data) {
            show_calendar(data);
        }
    });
}

function set_day(calendar_id, year, month, day, state) {
    var day_id = month.toString().padStart(2, 0) + "-" + day.toString().padStart(2, 0);

    $.ajax({
        url: calendarURL + "calendars/"+calendar_id+"/"+year+'/'+month+'/'+day+"/"+state,
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
    $.get(calendarURL + "calendars", function(data) {
        display_calendar_list(data);
        $.get(calendarURL + "display", function (display_data) {
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
        $.get(calendarURL + "calendars/" + $(this).parent().data("id"), function (data) {
            $("#calendar-name").val(data.name);
            $("#calendar-edit").modal('show');
            $('#calendar-edit form').attr('action', calendarURL + 'calendars/'+data.id);
            setTimeout(function(){ pickr.setColor('rgb('+ data.color +')'); }, 250);
        });
    });

    $("#calendar_list .btn-add").on("click", function () {
        $("#calendar-edit").modal('show');
        $("#calendar-name").val("");
        $('#calendar-edit form').attr('action', calendarURL + 'calendars');
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

$(document).ready(function() {
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
                $.get(calendarURL + "display/calendar", show_calendar);
            }
        });
        $("#calendar-edit").modal("hide");
    });
});
