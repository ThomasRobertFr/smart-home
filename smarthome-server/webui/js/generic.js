'use strict';

const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const dayNamesShort = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const monthNamesShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const apiURL = "/api/"
const calendarURL = "http://192.168.1.10/calendar/"
const domoticzAPI = "http://192.168.1.10:8080/json.htm?"

// updates to perform [fct, interval (s), lastUpdateField]
var updates = [];

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

$(document).ready(function() {
    setInterval(intervals, 1000);
    $('[data-toggle="tooltip"]').tooltip({container: 'body'});
});

