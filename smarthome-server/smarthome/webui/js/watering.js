"use strict";

var chart;

function showCharts(tr, data) {
    if ($('#chart-'+data.id).length > 0) {
        $('#chart-'+data.id).remove();
        return;
    }

    tr.after('<tr id="chart-'+data.id+'"><td colspan="7"><div class="chart-top"></div>'+
             '<div class="chart-line"></div></td></tr>');

    var i;
    var measures = JSON.parse(JSON.stringify(data.measures));
    var waterings = JSON.parse(JSON.stringify(data.waterings));
    var calibrations = JSON.parse(JSON.stringify(data.calibrations));
    for (i = 0; i < measures.length; i++) {
        measures[i][0] *= 1000;
        measures[i][1] = 100 * (data.calibration_max - measures[i][1]) / (data.calibration_max - data.calibration_min);
        measures[i][1] = Math.round(measures[i][1]);
    }
    for (i = 0; i < waterings.length; i++) {
        waterings[i][0] *= 1000;
        waterings[i][1] = Math.round(waterings[i][1]);
    }
    for (i = 0; i < calibrations.length; i++) {
        calibrations[i][0] = (calibrations[i][0] + i) * 1000;
        calibrations[i][1] = Math.round(calibrations[i][1]);
    }

    var options = {
        chart: {id: data.id+'-chart', height: 250, width: "100%", type: "area", stacked: false, animations: {enabled: false}},
        series: [
            {name: 'humidity', type: 'area', data: measures},
            {name: 'waterings', type: 'scatter', data: waterings},
            {name: 'calibrations', type: 'scatter', data: calibrations},
        ],
        xaxis: {
            type: 'datetime'
        },
        markers: {
          size: [3, 8, 3],
          strokeWidth: [1, 0, 0],
          hover: {sizeOffset: 1}
        },
        stroke: {
            show: [true, true, false],
            width: [2, 2, 0]
        },
        tooltip: {
            enabledOnSeries: [0, 1, 2],
            shared: false,
            x: {format: "dd MMM HH:mm"}
        },
        dataLabels: {
          enabled: true,
          enabledOnSeries: [0, 1, 2],
          offsetY: -6,
        },
        fill: {
            type: ["gradient", "solid", "solid"]
        },
        yaxis: [
            {show: false, min: 0, max: 100},
            {show: false, seriesName: 'waterings'},
            {show: false, seriesName: 'calibrations', min: 0, max: 1200}
        ]
    }
    chart = new ApexCharts(document.querySelector("#chart-"+data.id+" div.chart-top"), options);
    chart.render();
    chart.hideSeries('calibrations');

    var optionsLine = {
        series: [{data: measures}],
        chart: {
            id: data.id+'-chart-line',
            height: 100,
            type: 'area',
            brush: {target: data.id+'-chart', enabled: true},
            selection: {
                enabled: true,
                xaxis: {
                    min: Date.now() - 7*24*60*60*1000,
                    max: Date.now()
                }
            },
        },
        xaxis: {type: 'datetime', tooltip: {enabled: false}},
        yaxis: {show: false, min: 0, max: 100, tickAmount: 1}
    };

    var chartLine = new ApexCharts(document.querySelector("#chart-"+data.id+" div.chart-line"), optionsLine);
    chartLine.render();
}

function editItem(id, key) {
    var val = $("#sensors").data("sensors")[id][key];
    var new_val = prompt("Enter new value for " + id + " / " + key, val);
    if (new_val == null)
        return;
    var req = $.ajax({
        type: "PATCH",
        url: "/api/watering/" + id + "?" + $.param({"key": key, "value": new_val}),
        async: false
    });

    if (req.status == 200)
        return req.responseText;
    else
        return val + " (ERROR)";
}

function deleteSensor(id) {
    $.ajax({
        type: "DELETE",
        url: "/api/watering/" + id
    });
}

function showValue(val, show, append) {
    if (show == "class_hide_if_false")
        return (val == "false" || val == "f" || val == "no" || !val) ? "hidden" : "";
    if (show == "class_hide_if_true")
        return (val == "false" || val == "f" || val == "no" || !val) ? "" : "hidden";
    if (show == "class_invisible_if_false")
        return (val == "false" || val == "f" || val == "no" || !val) ? "invisible" : "";

    if (show == "waterings_last_val") {
        if (val.length > 0)
            val = val[val.length - 1][1];
        else
            return "?";
    }
    if (show == "humidity_last_val") {
        if (val["measures"].length == 0)
            return "?";
        val = Math.round(
            100 * (val["calibration_max"] - val["measures"][val["measures"].length - 1][1]) /
            (val["calibration_max"] - val["calibration_min"])
        );
    }
    if (show == "humidity_last_time") {
        if (val.length > 0) {
            val = Math.round(Date.now() / 1000) - val[val.length - 1][0];
            show = "h_min";
        }
        else
            return "never";
    }
    if (show == "h_min" || show == "h") {
        var val_min = Math.round(val / 60);
        if (val_min < 60) {
            if (show == "h")
                val = (val_min == 0) ? "0h" : "0h" + String(val_min).padStart(2, "0");
            else if (val_min == 0)
                val = "< 1 min";
            else
                val = val_min + " min";
        }
        else if (val_min > 60 * 72)
            val = Math.round(val_min / 60 / 24) + "d";
        else {
            var val_h = Math.floor(val_min / 60);
            val_min = Math.floor(val_min % 60);
            val = (val_min > 0) ? val_h + "h" + String(val_min).padStart(2, '0') : val_h + "h";
        }
    }

    var icons_mapping = {
        "icons-water": "fa-shower",
        "icons-calibr": "fa-compass",
        "icons-sensor": "fa-tachometer-alt-fast",
        "icons-sched": "fa-clock",
    };
    var icons_mapping_off = {
        "icons-calibr": "fa-compass-slash",
        "icons-sensor": "fa-tachometer-slowest",
    };
    if (icons_mapping[show]) {
        if (val == "false" || val == "f" || val == "no" || !val) {
            if (icons_mapping_off[show])
                val = '<i class="fad fa-fw '+icons_mapping_off[show]+' icon-off"></i>';
            else
                val = '<span class="fa-stack icon-off"><i class="fad '+icons_mapping[show]+' fa-stack-1x"></i><i class="fas fa-slash fa-stack-1x"></i></span>';
        }
        else
            val = '<i class="fad fa-fw '+icons_mapping[show]+' icon-on"></i>';
    }

    if (append) {
        val += append;
    }

    return val;
}

function activateButtons() {
    $("tr.sensor").unbind("click").on("click", function () {
        var id = $(this).data("id");
        showCharts($(this), $("#sensors").data("sensors")[id]);
    })

    $(".btn-remove").unbind("click").on("click", function (e) {
        e.stopPropagation();
        var tr = $(this).parent().parent();
        var id = tr.data("id");
        if (window.confirm("Delete "+id+"?")) {
            deleteSensor(id);
            tr.remove();
        }
    });

    $(".btn-edit").unbind("click").on("click", function (e) {
        e.stopPropagation();
        // var id = $(this).parent().parent().data("id");
        var tr = $($(this).parent().parent().parent().parent());

        tr.toggleClass("edit-active");

        $(".field").unbind("click");
        $(".edit-active .field").on("click", function (e) {
            e.stopPropagation();
            var out = editItem($(this).data("id"), $(this).data("key"));
            $(this).empty().append(out);
        });
    });
}

function addLine(data) {
    var html = '<tr class="sensor" data-id="'+data.id+'">';
    html += document.getElementById("sensor-pattern").innerHTML.replace(
        new RegExp(/\{(.+?)\}/g),
        function (x) {
            var args = x.slice(1, -1).split(",");
            var span = (!(typeof args[1] == "string" && args[1].includes("class")) && args[0] != "id" && args[0] != "all" && !Array.isArray(data[args[0]]));
            var out = span ? '<span class="field" data-id="'+data.id+'" data-key="'+args[0]+'">' : '';
            out += showValue(args[0] == "all" ? data : data[args[0]], args[1], args[2]);
            out += span ? '</span>' : '';
            return out;
        }
    );
    html += "</tr>";
    $("#sensors tbody").append(html);

    var measures_sparkline = [];
    var waterings_times_annotations = [];
    var nb_days_shown = 5;
    var measures = data.measures;
    for (var i = 0; i < measures.length; i++) {
        var time = measures[i][0] * 1000;
        if (time > Date.now() - nb_days_shown * 24 * 60 * 60 * 1000)
            measures_sparkline.push([time, Math.round(
            100 * (data.calibration_max - measures[i][1]) /
                (data.calibration_max - data.calibration_min)
            )]);
    }
    for (var i = 0; i < data.waterings.length; i++) {
        var time = data.waterings[i][0] * 1000;
        if (time > Date.now() - nb_days_shown * 24 * 60 * 60 * 1000) {
            waterings_times_annotations.push({
                x: time, borderColor: '#00e396', strokeDashArray: 0, borderWidth: 1.6
            });
        }
    }
    var options = {
        series: [{data: measures_sparkline}],
        chart: {type: 'area', width: 55, height: 22, sparkline: {enabled: true}, animations: {enabled: false}},
        yaxis: {show: false, min: -8, max: 108},
        xaxis: {type: 'datetime'},
        annotations: {
            yaxis: [
                {y: data.watering_humidity_target, borderColor: '#00E396', strokeDashArray: 0, borderWidth: 1.6},
                {y: data.watering_humidity_threshold, borderColor: '#FEB019', strokeDashArray: 0, borderWidth: 1.6}
            ],
            xaxis: waterings_times_annotations,
        },
        stroke: {width: 2},
        tooltip: {enabled: false}
    };
    var chart = new ApexCharts(document.querySelector("#sparkline-"+data.id), options);
    chart.render();
    activateButtons();
}

$(document).ready(function (){
    $.get("/api/watering?full=true", function (data) {
        $("#sensors").data("sensors", data);
        for (var id in data) {
            addLine(data[id]);
        }
    });

    $("#form_add").on("submit", function (e) {
        e.preventDefault();
        var id = $("#new_id").val();
        var url = $("#form_add").attr('action') + id;

        $.ajax({
            type: "POST",
            url: "/api/watering/"+ id +"?full=true",
            success: function(data) {
               addLine(data);
               $("#sensors").data("sensors")[id] = data;
            }
        });
    });
});
