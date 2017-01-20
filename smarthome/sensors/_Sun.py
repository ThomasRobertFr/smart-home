from flask_restful import Resource
import math
from babel.dates import format_date
from datetime import datetime, timedelta
from ..misc import config as _config
config = _config.get().location


class Sun(Resource):

    def _get_elevation(self, date=datetime.now(), time_N=100):
        # params
        lat = math.radians(config.latitude)
        long = math.radians(config.longitude)
        tz = config.timezone
        day = date.toordinal() + 2 - datetime(1900, 1, 1).toordinal()

        # consts
        eliptic = math.radians(23)
        var_y = math.tan(eliptic / 2) ** 2
        eccent_earth = 0.016708634

        # day
        julian_day = day + 2415018.5 - tz / 24
        julian_century = (julian_day - 2451545) / 36525

        # sun parameters
        sun_long = math.radians(280.46646 + julian_century * (36000.76983 + julian_century * 0.0003032) % 360)
        sun_anom = math.radians(357.52911 + julian_century * (35999.05029 - 0.0001537 * julian_century))
        sun_declin = math.asin(math.sin(eliptic) * math.sin(sun_long))
        eq_of_time = 4 * math.degrees(var_y * math.sin(2 * sun_long) - 2 * eccent_earth * math.sin(sun_anom)
                                      + 4 * eccent_earth * var_y * math.sin(sun_anom) * math.cos(2 * sun_long)
                                      - 0.5 * var_y ** 2 * math.sin(4 * sun_long)
                                      - 1.25 * eccent_earth ** 2 * math.sin(2 * sun_anom))

        # ha_sunrise = math.acos(math.cos(1.585335) / (math.cos(lat) * math.cos(sun_declin))
        #                       - math.tan(lat) * math.tan(sun_declin))
        # solarNoon = (720-4*math.degrees(long) - eq_of_time + tz * 60) / 1440
        # sunRadVector = 1.000001018 * (1 - eccent_earth**2) / (1 + eccent_earth * math.cos(sun_anom))
        # sunRtAscent = math.atan2(math.cos(eliptic) * math.sin(sun_long), math.cos(sun_long))
        # sunriseTime = solarNoon-math.degrees(ha_sunrise) * 4 / 1440
        # sunsetTime = solarNoon+math.degrees(ha_sunrise) * 4 / 1440

        solar_elevation = []
        for i in range(time_N):
            time_i = float(i) / time_N
            true_solar_time = (time_i * 1440 + eq_of_time + 4 * math.degrees(long) - 60 * tz) % 1440
            hour_angle = true_solar_time / 4
            hour_angle += 180 if true_solar_time / 4 > 0 else -180
            solar_elevation_i = 90 - math.degrees(math.acos(math.sin(lat) * math.sin(sun_declin) + math.cos(lat) *
                                                            math.cos(sun_declin) * math.cos(math.radians(hour_angle))))
            solar_elevation.append(solar_elevation_i)

        return solar_elevation

    def get(self):
        return self._get_elevation()

    def get_svg(self):
        # plot config
        width = 3000
        height = 175
        horizon = 120
        y_scale = -1.8

        # elevation infos
        nb_pts = 100
        nb_days = 5
        date = datetime.today() - timedelta(days=2)  # init
        dx_true = width / (nb_pts * nb_days)
        dx_dilation = 600. / (dx_true * nb_pts)  # 600px days
        dx = dx_true * dx_dilation

        # elevations data
        elevations = []
        for i in range(nb_days):
            elevations += self._get_elevation(date=date, time_N=nb_pts)
            date += timedelta(days=1)

        # elevation path
        elevations_path = "M0 %.2f " % (horizon + elevations[0] * y_scale)
        for i in range(1, len(elevations)):
            elevations_path += "l %.2f %.2f " % (dx, (elevations[i] - elevations[i - 1]) * y_scale)

        # x lines
        x_lines = ""
        for i in range(-50, 91, 10):
            if i != 0:
                x_lines += '<line class="x_line" x1="0" x2="{width}" y1="{pos}" y2="{pos}"/>'.format(width=width, pos=horizon + i * y_scale)

        # x ticks & days
        dx_1h = dx * nb_pts / 24
        x_ticks = ""
        for i in range(nb_days):
            for j in range(24):
                if j == 0:
                    x_ticks += '<line class="x_tick_large" x1="{pos}" x2="{pos}" y1="0" y2="{height}"/>'.format(
                        pos=dx_1h * (i * 24 + j), height=height)
                    x_ticks += ('<text class="day_txt" transform="translate({posx} {posy}) rotate(270)">'+format_date(datetime.today() + timedelta(days=i-2), "d MMMM", locale="fr")+'</text>').format(
                        posx=dx_1h * (i * 24 + j) + 10, posy=horizon-5)
                else:
                    x_ticks += '<line class="x_tick" x1="{pos}" x2="{pos}" y1="{y1}" y2="{y2}"/>'.format(
                        pos=dx_1h * (i * 24 + j), y1=horizon-3, y2=horizon + 3)
                    x_ticks += '<text x="{pos}" y="{y}" class="x_tick_text">{time}h</text>'.format(
                        pos=dx_1h * (i * 24 + j), y=horizon + 15, time=j)

        # elevation index for right now (2 days + day fraction of current day) * pts_per_day
        now = datetime.now() # - timedelta(hours=8)
        now_i = math.floor(nb_pts * (2 + timedelta(hours=now.hour, minutes=now.minute).total_seconds() / 24 / 3600))

        # sun
        sun_x = now_i*dx
        sun_y = horizon + elevations[now_i] * y_scale
        sun_elev = int(round(elevations[now_i], 0))
        sun_shadow = max(0, 15 - math.fabs(elevations[now_i] - 5)) * 1.0 / 12.0 # 0 at -10deg -> 15 at 5deg -> 0 at 20deg

        # gradient
        horizon_ratio = (height - horizon) * 1.0 / height
        gradient = '<stop offset="0" style="stop-color:#00081D"/>' \
                   '<stop offset="'+str(0.45*horizon_ratio)+'" style="stop-color:#012D5E"/>' \
                   '<stop offset="'+str(0.65*horizon_ratio)+'" style="stop-color:#013F72"/>' \
                   '<stop offset="'+str(0.8*horizon_ratio)+'" style="stop-color:#145788"/>' \
                   '<stop offset="'+str(0.98*horizon_ratio)+'" style="stop-color:#2872A1"/>' \
                   '<stop offset="'+str(horizon_ratio + 0.02*(1-horizon_ratio))+'" style="stop-color:#ED9C4F"/>' \
                   '<stop offset="'+str(horizon_ratio + 0.08*(1-horizon_ratio))+'" style="stop-color:#FABF63"/>' \
                   '<stop offset="'+str(horizon_ratio + 0.15*(1-horizon_ratio))+'" style="stop-color:#FFDC81"/>' \
                   '<stop offset="'+str(horizon_ratio + 0.3*(1-horizon_ratio))+'" style="stop-color:#F3E6C6"/>' \
                   '<stop offset="'+str(horizon_ratio + 0.5*(1-horizon_ratio))+'" style="stop-color:#EAE6DE"/>' \
                   '<stop offset="'+str(horizon_ratio + 0.9*(1-horizon_ratio))+'" style="stop-color:#D7E5F8"/>'

        out = """
                <?xml version="1.0" encoding="utf-8"?>
                <svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
                        width="{width}px" height="{height}px">
                    <style type="text/css">
                    .x_line {{ stroke: grey; stroke-width: 1; stroke-dasharray: 1,5; opacity: 0.5 }}
                    .x_tick {{ stroke: white; stroke-width: 1.5; opacity: 0.8; }}
                    .x_tick_large {{ stroke: black; stroke-width: 1.5; stroke-dasharray: 3,5; opacity: 0.3; }}
                    .x_tick_text {{ fill: white; font-size: 9px; font-family: Comfortaa, sans-serif; text-anchor: middle; opacity: 0.8; }}
                    .day_txt {{ fill: black; font-size: 10px; font-family: Comfortaa, sans-serif; text-anchor: left; opacity: 0.4; }}
                    #elevation {{ fill: none; stroke: black; stroke-width: 1.5; stroke-dasharray: 1.5,1.5; opacity: 0.7; }}
                    #sun {{ filter: url(#dropshadow); }}
                    #sun_elev_txt {{ fill: {sun_txt_color}; font-size: 10px; font-family: Comfortaa, sans-serif; opacity: 1 }}
                    </style>
                    <defs>
                        <linearGradient id="bg-grad" x1="0" x2="0" y1="1" y2="0">
                            {gradient}
                        </linearGradient>
                        <filter id="dropshadow">
                          <feColorMatrix result="matrixOut" in="SourceGraphic" type="matrix"
                            values="0.2 0 0 0 0 0 0.2 0 0 0 0 0 0.2 0 0 0 0 0 1 0" />
                          <feGaussianBlur in="matrixOut" stdDeviation="{sun_shadow}"/> <!-- stdDeviation is how much to blur -->
                          <feMerge>
                            <feMergeNode/> <!-- this contains the offset blurred image -->
                            <feMergeNode in="SourceGraphic"/> <!-- this contains the element that the filter is applied to -->
                          </feMerge>
                        </filter>
                    </defs>
                    <rect id="background" x="0" y="0" fill="url(#bg-grad)" width="{width}" height="{height}"/>
                    {x_lines}
                    <!--<line x1="0" x2="{width}" y1="{horizon}" y2="{horizon}" stroke="#000000" stroke-width="3"/>-->
                    <g transform="translate(0)">
                        <path id="elevation" d="{elevations}"/>

                        {x_ticks}

                        <text x="{sun_txt_x}" y="{sun_txt_y}" id="sun_elev_txt">{sun_elev}°</text>

                        <g id="sun">
                            <g transform="translate({sun_x} {sun_y}) scale(0.0065)">
                                <defs>
                                    <path id="sun_borders" d="M1716.248,1711.868c-390.521,391.604-1023.702,391.604-1414.233-0.018
                                        c-390.521-391.607-390.521-1026.521,0-1418.155c390.531-391.602,1023.681-391.602,1414.233,0.049
                                        C2106.742,685.3,2106.777,1320.243,1716.248,1711.868z"/>
                                </defs>
                                <use xlink:href="#sun_borders" overflow="visible" fill="#F5B81C"/>
                                <clipPath id="sun_borders_clip">
                                    <use xlink:href="#sun_borders"  overflow="visible"/>
                                </clipPath>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#904920" points="1784.238,1804.481 1992.713,1332.397 1913.055,1220.829"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FBCE2C" points="1367.207,-22.314 1160.541,319.253 553.033,620.746 261.161,225.796"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F3981F" points="1462.584,1446.019 726.042,2049.204 309.938,1095.468"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#A34F24" points="1647.57,1656.915 1462.584,1446.019 726.042,2049.204"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E27E26" points="1464.051,1456.099 1144.635,259.915 1395.961,388.54 1594.633,488.511 2081.828,737.409"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#ECA821" points="1144.635,259.915 1462.584,1446.019 309.938,1095.468"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F09121" points="2068.213,729.086 1351.693,-24.159 1144.635,259.915 1386.738,407.127 1594.633,488.511"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#DC7427" points="2078.236,729.086 1941.686,1290.579 1647.57,1656.915 1462.584,1446.019"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#A34E24" points="726.042,2049.204 217.928,1717.108 -93.719,1105.065 309.938,1095.468 "/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCDB43" points="1144.635,259.915 312.81,1101.813 230.246,800.565 184.496,644.999 261.161,225.796 539.342,237.815"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FAB719" points="312.81,1101.813 -93.719,1105.065 261.161,225.796 187.274,645.154 235.21,797.594"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#D95B26" points="1365.24,-24.753 1803.797,295.4 1594.633,488.511"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E37D25" points="1803.797,295.4 2083.898,742.967 1594.633,488.511"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EA7D24" points="217.928,1717.108 315.12,1101.456 -94.557,1104.987"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FFC541" points="1144.635,259.915 855.728,722.08 788.047,512.171"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#ECA92A" points="1876.316,963.76 1599.291,895.207 1488.48,903.692 1462.584,1446.019"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E06926" points="2083.727,732.542 1876.316,963.76 1599.291,895.207"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#D96D27" points="1876.316,963.76 1823.418,1199.708 1462.584,1446.019"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#974021" points="2086.91,727.521 1992.713,1332.397 1823.418,1199.708"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#A34F24" points="1647.57,1656.915 1783.146,1808.757 1941.686,1290.579"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#9B4722" points="1784.238,1804.481 1269.771,2024.183 1319.92,1846.567"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#B45026" points="678.3,2052.911 1274.291,2024.202 1319.92,1846.567"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FED730" points="261.161,225.796 539.342,237.815 418.901,292.257 251.799,338.764"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FDB61A" points="261.161,225.796 719.834,-9.289 885.207,128.652"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCD031" points="885.207,128.652 539.342,237.815 261.161,225.796"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F9BF50" points="261.161,225.796 150.154,321.219 195.974,383.708"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F7C22E" points="1378.398,-22.066 885.207,128.652 719.834,-9.289"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EFC276" points="251.799,338.764 59.985,550.72 150.154,321.219"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FFF3B3" points="-94.557,1104.987 59.985,550.72 103.497,615.459"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FDDA32" points="251.799,338.764 286.486,497.771 59.985,550.72"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F5A31D" points="312.81,1101.813 622.397,1191.452 454.223,1031.212"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EE8E22" points="622.397,1191.452 539.061,1621.554 312.81,1101.813"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EE9C21" points="726.042,2049.204 487.535,1620.149 312.81,1101.813"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E38B25" points="1647.57,1656.915 1221.209,1642.714 1462.584,1446.019"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E07926" points="1462.584,1446.019 1319.92,1846.567 721.518,2050.909"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F9C434" points="217.928,1717.108 487.535,1620.149 312.81,1101.813"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E98B24" points="1025.174,1312.991 721.518,2050.909 1462.584,1446.019"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FEECE0" points="187.274,645.154 40.052,610.927 62.228,547.059 178.257,493.673 246.22,540.241"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FDD323" points="246.22,540.241 178.257,493.673 286.486,497.771 414.61,479.693"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FDD97C" points="631.662,436.017 533.442,462.46 582.225,579.165 668.25,447.447"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#904920" points="553.033,620.746 529.451,778.393 707.951,865.058"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FAD03A" points="529.451,778.393 451.108,855.813 707.951,865.058"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCD71F" points="788.047,512.171 855.728,722.08 707.951,865.058 553.033,620.746 582.225,579.165 668.25,447.447"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FEE233" points="414.61,479.693 187.274,645.154 246.22,540.241"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F4B31B" points="616.914,1189.901 454.223,1031.212 451.108,855.813 707.951,865.058 781.901,879.771 703.958,1018.482"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F7C529" points="781.901,879.771 855.728,722.08 1001.976,799.849"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EA9E22" points="1462.584,1446.019 1183.781,985.169 1334.611,758.25 1500.605,845.979"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FACA27" points="1001.976,799.849 703.958,1018.482 781.901,879.771"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCCF1E" points="668.25,447.447 1144.635,259.915 788.047,512.171"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FBCC1E" points="631.662,436.017 539.342,237.815 1144.635,259.915 668.25,447.447"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCCB28" points="414.61,479.693 418.901,292.257 251.799,338.764 286.486,497.771"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EFA120" points="1223.928,924.771 1599.291,895.207 1386.738,407.127"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F5B81C" points="1386.738,407.127 855.728,722.08 1001.976,799.849 1223.928,924.771"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F3BA27" points="1158.084,777.924 1223.928,924.771 1183.781,985.169 1001.976,799.849"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F0B11D" points="1223.928,924.771 1158.084,777.924 1386.738,407.127"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#9E4422" points="1599.291,895.207 1594.633,488.511 1821.258,603.635"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#EFA520" points="1183.781,985.169 1025.174,1312.991 1001.976,799.849"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#F5B71C" points="703.958,1018.482 616.914,1189.901 1025.174,1312.991"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCD679" points="451.108,855.813 312.81,1101.813 454.223,1031.212"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#DB9529" points="529.451,778.393 187.274,645.154 451.108,855.813"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#FCD22A" points="187.274,645.154 553.033,620.746 582.225,579.165 533.442,462.46 414.61,479.693"/>
                                <polygon clip-path="url(#sun_borders_clip)" fill="#E58124" points="539.061,1621.554 1025.174,1312.991 722.425,2072.849"/>
                            </g>
                        </g>
                    </g>
                    <!-- {debug} -->
                </svg>
                """.format(horizon=horizon, width=width, height=height, night=height - horizon, gradient=gradient,
                           elevations=elevations_path, x_lines=x_lines, x_ticks=x_ticks,
                           sun_x=sun_x-6.5, sun_y=min(height-3, sun_y-6.5),
                           sun_txt_x=sun_x+11, sun_txt_y=min(height-3, sun_y+3.5),
                           sun_txt_color="black" if sun_elev > 0 else "white", sun_elev=sun_elev, sun_shadow=sun_shadow,
                           debug=str(now))

        return out.strip()




