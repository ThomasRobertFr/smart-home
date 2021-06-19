"use strict";

var chart;

function addLine(data) {
    var humidity = "?";
    var humidity_delta_mins = 0;
    var humidity_delta = "?";
    var watered = "";
    var wateringNeeded = false;

    if (data.measures.length) {
        var last_measure = data.measures[data.measures.length - 1];
        humidity = Math.round(
                100 * (data.calibration_max - last_measure[1]) /
                (data.calibration_max - data.calibration_min)
            );
        humidity_delta_mins = Math.round((Math.round(Date.now() / 1000) - last_measure[0]) / 60);
        if (humidity_delta_mins < 60)
            humidity_delta = humidity_delta_mins + " min";
        else
            humidity_delta = Math.floor(humidity_delta_mins / 60) + "h" +
                             String(Math.floor(humidity_delta_mins % 60)).padStart(2, '0');
        if (humidity < data.watering_humidity_threshold)
            wateringNeeded = true;
    }
    if (data.watering_last_delta) {
        watered = Math.round(data.watering_last_delta / 60 / 60 / 24);
        if (watered > 30)
            watered = "";
        else if (watered > 0)
            watered = watered + 'd ago';
        else
            watered = 'today';
    }

    var html = '<tr>'; // data.id
    html += '<td><span class="sparkline" id="sparkline-'+ data.id + '"></span></td>';
    html += '<td class="name">' + data.id + '</td>';
    html += '<td class="measure"><span data-toggle="tooltip" title="'+humidity_delta+' ago">';
    html += '<i class="fad fa-humidity"></i> ' + humidity + '%';
    if (humidity_delta_mins > data.measure_interval * 1.5 / 60) // warn if too long ago
        html += ' <i class="fas fa-battery-slash alert-color"></i>';
    html += '</span></td>';
    html += '<td class="watered"><span data-toggle="tooltip" title="Target: '+data.watering_humidity_threshold+'%">';
    if (watered && !wateringNeeded)
        html += '<i class="fad fa-shower"></i> ';
    else if (wateringNeeded)
        html += '<i class="fad fa-shower alert-color"></i> ';
    if (watered)
        html += watered;
    html += "</span></td></tr>";
    $("#waterings").append(html);
    $('[data-toggle="tooltip"]').tooltip({container: 'body'});

    var measures_sparkline = [];
    var waterings_times_annotations = [];
    var measures = data.measures;
    var nb_days_shown = 5;
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
}

$(document).ready(function (){
    $.get("/api/watering?full=true", function (data) {
        $("#waterings").empty();
        for (var id in data) {
            addLine(data[id]);
        }
    });
});
