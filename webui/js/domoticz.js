'use strict';

updates = updates.concat([
    [updateDomoticz, 15, 0],
]);

function hsvToRgb(h, s, v) {
  var r, g, b;

  var i = Math.floor(h * 6);
  var f = h * 6 - i;
  var p = v * (1 - s);
  var q = v * (1 - f * s);
  var t = v * (1 - (1 - f) * s);

  switch (i % 6) {
    case 0: r = v, g = t, b = p; break;
    case 1: r = q, g = v, b = p; break;
    case 2: r = p, g = v, b = t; break;
    case 3: r = p, g = q, b = v; break;
    case 4: r = t, g = p, b = v; break;
    case 5: r = v, g = p, b = q; break;
  }

  return [ r * 255, g * 255, b * 255 ];
}

function rgbToHsv(r, g, b) {
  r /= 255, g /= 255, b /= 255;

  var max = Math.max(r, g, b), min = Math.min(r, g, b);
  var h, s, v = max;

  var d = max - min;
  s = max == 0 ? 0 : d / max;

  if (max == min) {
    h = 0; // achromatic
  } else {
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }

    h /= 6;
  }

  return [ h, s, v ];
}


function updateDomoticz() {
    /** Update the webpage state based on Domoticz status */
    $.get(domoticzAPI + "type=devices&filter=all&used=true&order=Name", function(data) {
        var devices = data["result"];
        var hue_idx = $("#hue_hs_container").data("idx");
        for (var i in devices) {
            if (devices[i].Status == "Off") {
                $('.switch[data-idx='+devices[i].idx+']').find(".toggle").removeClass("checked");
            }
            else {
                $('.switch[data-idx='+devices[i].idx+']').find(".toggle").addClass("checked");
            }
            $('.slider[data-idx='+devices[i].idx+']').find("input").val(devices[i].LevelInt);
            if (devices[i].idx == hue_idx) {
                var color = JSON.parse(devices[i].Color);
                var hsv = rgbToHsv(color["r"], color["g"], color["b"]);
                var rho = hsv[1];
                var phi = hsv[0] * 2 * Math.PI - Math.PI;
                var y = rho * Math.cos(phi);
                var x = rho * Math.sin(phi);
                $("#hue_hs_pos").css("left", ((x + 1)*50)+"%");
                $("#hue_hs_pos").css("top", ((y + 1)*50)+"%");
            }
        }
    });
}

function runToggle(el) {
    el = $(el).parents(".switch");
    var state = el.find(".toggle").hasClass("checked") ? "On" : "Off";
    $.get(domoticzAPI + "type=command&param=switchlight&idx=" + el.data('idx') + "&switchcmd=" + state);
}


$(document).ready(function() {
    // SWITCHES
    $('.switch .toggle').click(function () { vibrate();
        $(this).toggleClass("checked");
        runToggle(this);
    });
    $('.switch .toggle-container .before').click(function () { vibrate(); // "ON" text
        $(this).parent().find('.toggle').removeClass("checked");
        runToggle(this);
    });
    $('.switch .toggle-container .after').click(function () { vibrate(); // "OFF" text
        $(this).parent().find('.toggle').addClass("checked");
        runToggle(this);
    });

    // SLIDERS
    $('.slider input[type=range]').change(function () { vibrate();
        var idx = $(this).parents(".slider").data('idx');
        $.get(domoticzAPI + "type=command&param=switchlight&idx=" + idx + "&switchcmd=Set%20Level&level=" + $(this).val());
        $('.switch[data-idx='+idx+']').find(".toggle").addClass("checked");
    });

    // PUSH BUTTONS
    $('.push-button').click(function () { vibrate();
        var idx = $(this).data('idx');
        $.get(domoticzAPI + "type=command&param=switchlight&idx=" + idx + "&switchcmd=On");
    });

    // COLOR
    $("#hue_hs").click(function (e) {
        var x = e.offsetX / $(this).width() * 2 - 1;
        var y = e.offsetY / $(this).height() * 2 - 1;
        var rho = Math.min(Math.sqrt(x*x + y*y), 1);
        var phi = Math.atan2(x, y) + Math.PI;
        var hue_h = phi / Math.PI / 2; // * 65535;
        var hue_s = rho; // * 255;
        $("#hue_hs_pos").css("left", ((rho * Math.sin(phi - Math.PI) + 1)*50)+"%");
        $("#hue_hs_pos").css("top", ((rho * Math.cos(phi - Math.PI) + 1)*50)+"%");
        var rgb = hsvToRgb(hue_h, hue_s, 1);
        var idx = $("#hue_hs_container").data("idx");
        var colorStr = '{"m":3,"t":0,"r":' + Math.round(rgb[0]) + ',"g":' + Math.round(rgb[1]) + ',"b":' + Math.round(rgb[2]) + ',"cw":0,"ww":0}';
        var bri = $('.slider[data-idx='+idx+'] input[type=range]').val();
        $.get(domoticzAPI + "type=command&param=setcolbrightnessvalue&idx=" + idx + "&color=" + encodeURIComponent(colorStr) + "&brightness=" + bri);
    });
});
