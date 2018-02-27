# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
#   pysk is a ncurses client for SignalK
#   Copyright (C) 2016  Philip J Freeman <elektron@halo.nu>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import math
import os
import time

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime
from papirus import Papirus


def wind_widget(name, gauge_radius, font, angle, speed, convert_units=[]):
    """wind angle and speed widget"""

    text_size = (gauge_radius/3)+1
    gauge_width = gauge_radius*2+1
    gauge_height = gauge_radius*2+1+text_size*2

    out_image = Image.new("L", (gauge_width,gauge_height), 255)
    draw = ImageDraw.Draw(out_image)
    draw.ellipse((1,1,gauge_width-1,gauge_width-1), outline=0)

    gauge_origin = (gauge_radius, gauge_radius)
    gauge_point = (
        gauge_radius+int(gauge_radius*math.cos(angle.value-(math.pi/2))),
        gauge_radius+int(gauge_radius*math.sin(angle.value-(math.pi/2)))
        )
    draw.line([gauge_origin, gauge_point], fill=0)
    draw.text((1, gauge_width),name, font=font)
    draw.text((10, gauge_width+text_size*1), speed.display_value(convert_units=convert_units), font=font)
    return out_image


def interface_main(*args, **kwargs):
    """papirus ui"""

    SK_CLIENT = kwargs['sk_client']

    user = os.getuid()
    if user != 0:
        logging.error("PaPiRus requires root perms to run, supossedly...")
        return 1

    WHITE = 255
    BLACK = 0

    # fonts are in different places on Raspbian/Angstrom so search
    possible_fonts = [
        '/usr/share/fonts/truetype/unifont/unifont.ttf',
        '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono-Bold.ttf',   # R.Pi
        '/usr/share/fonts/truetype/freefont/FreeMono.ttf',                # R.Pi
        '/usr/share/fonts/truetype/LiberationMono-Bold.ttf',              # B.B
        '/usr/share/fonts/truetype/DejaVuSansMono-Bold.ttf',              # B.B
        '/usr/share/fonts/TTF/FreeMonoBold.ttf',                          # Arch
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'                        # Arch
    ]


    FONT_FILE = ''
    for f in possible_fonts:
        if os.path.exists(f):
            FONT_FILE = f
            break

    if '' == FONT_FILE:
        logging.ERROR('no font file found')
        return 1

    logging.info("selected font: {}".format(FONT_FILE))

    MAX_START = 0xffff

    papirus = Papirus()

    logging.info('panel = {p:s} {w:d} x {h:d}  version={v:s} COG={g:d} FILM={f:d}'.format(p=papirus.panel, w=papirus.width, h=papirus.height, v=papirus.version, g=papirus.cog, f=papirus.film))

    papirus.clear()

    # initially set all white background
    image = Image.new('1', papirus.size, WHITE)

    # prepare for drawing
    draw = ImageDraw.Draw(image)
    width, height = image.size

    gauge_radius = 48

    header_font = ImageFont.truetype(FONT_FILE, 20, encoding="unic")
    footer_font = ImageFont.truetype(FONT_FILE, 10, encoding="unic")
    gauge_font = ImageFont.truetype(FONT_FILE, gauge_radius/3, encoding="unic")

    # clear the display buffer
    draw.rectangle((0, 0, width, height), fill=WHITE, outline=WHITE)
    previous_second = 0

    vessel_self = SK_CLIENT.data.get_self()

    while True:

        now = datetime.today()


        # draw some shit
        # border
        draw.rectangle((2, 2, width - 2, height - 2), fill=WHITE, outline=BLACK)

        draw.text((10, height - 20), u"pysk:\u26F5 {}@{}".format(str(vessel_self),SK_CLIENT.server), fill=BLACK, font=footer_font)

        # apparent wind
        try:
            app_angle = vessel_self.get_datum('environment.wind.angleApparent')
            app_speed = vessel_self.get_datum('environment.wind.speedApparent')
        except:
            app_angle = None
            app_speed = None

        app_wind_gauge = wind_widget("Apparent",gauge_radius, gauge_font, app_angle, app_speed, convert_units=[('m/s', 'kn')])
        app_wind_gauge_width, app_wind_gauge_height = app_wind_gauge.size
        image.paste(app_wind_gauge,(10,10,10+app_wind_gauge_width,10+app_wind_gauge_height))

        # speed
        try:
            speed = vessel_self.get_datum('navigation.speedOverGround')
            speed_ground = speed.display_value(convert_units=[('m/s', 'kn')])
        except:
            speed_ground = u"\u2014"

        try:
            speed = vessel_self.get_datum('navigation.speedThroughWater')
            speed_water = speed.display_value(convert_units=[('m/s', 'kn')])
        except:
            speed_water = u"\u2014"

        draw.text((10+gauge_radius*2+3+10, 10 + 12*0),
                  u"\u03B3 \u2641: {}".format(speed_ground),
                  fill=BLACK, font=gauge_font)

        draw.text((10+gauge_radius*2+3+10, 10 + 12*1),
                  u"\u03B3 ~: {}".format(speed_water),
                  fill=BLACK, font=gauge_font)

        # pos
        try:
            lat = vessel_self.get_datum('navigation.position.latitude').display_value()
            lon = vessel_self.get_datum('navigation.position.longitude').display_value()
        except:
            lat = u"\u2014"
            lon = u"\u2014"

        draw.text((10+gauge_radius*2+3+10, 10 + 12*4),
                  u"\u2641: {}".format(lat),
                  fill=BLACK, font=gauge_font)
        draw.text((10+gauge_radius*2+3+10, 10 + 12*5),
                  u"   {}".format(lon),
                  fill=BLACK, font=gauge_font)

        # water temp
        try:
            temp = vessel_self.get_datum('environment.water.temperature')
            temp_water = temp.display_value(convert_units=[('K', 'F')])
        except:
            temp_water = u"\u2014"

        draw.text((10+gauge_radius*2+3+10, 10 + 12*9),
                  u"\u00B0 ~: {}".format(temp_water),
                  fill=BLACK, font=gauge_font)

        # depth
        try:
            depth = vessel_self.get_datum('environment.depth.belowTransducer')
            depth_string = depth.display_value(convert_units=[('m', 'ft')])
        except:
            depth_string = u"\u2014"

        draw.text((10+gauge_radius*2+3+10, 10 + 12*10),
                  u"\u2193 ~: {}".format(depth_string), fill=BLACK, font=gauge_font)

        # display image on the panel
        papirus.display(image)
        if now.second % 60 == 0:
            papirus.update()    # full update every minute
            logging.info("full screen updated")
        else:
            papirus.partial_update()
            logging.debug("partial screen updated")

        time.sleep(0.125)


def main():
    """main"""

    import sys

    from signalk_client.client import Client

    print """
python-signalk-client  Copyright (C) 2016  Philip J Freeman <elektron@halo.nu>
This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
are welcome to redistribute it under certain conditions.
"""

    global SK_CLIENT

    argparser = argparse.ArgumentParser(
        description="SignalK Client"
        )

    argparser.add_argument(
        'server',
        nargs='?',
        default=None,
        help='server to connect to',
        )

    argparser.add_argument(
        '-L', '--log-level',
        default="ERROR",
        help='debug level',
        )

    argparser.add_argument(
        '-i', '--interface',
        default="curses",
        help='ui interface type (console, curses, papirus)',
        )

    argparser.add_argument(
        '-D', '--log-file',
        default=None,
        help='log to file',
        )

    args = argparser.parse_args()

    # Setup Logging
    if args.log_file == None:
        log_stream = sys.stdout
    else:
        log_stream = open(args.log_file, "a")

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=args.log_level,
        stream=log_stream,
        )

    SK_CLIENT = Client(args.server)


    if args.interface == "console":
        logging.debug("interface console...")
        interface_console()
    elif args.interface == "curses":
        logging.debug("interface curses...")
        curses.wrapper(interface_curses)
    elif args.interface == "papirus":
        logging.debug("interface papirus...")
        interface_papirus()
    else:
        logging.error("unknown interface: {}".format(args.interface))

    logging.debug("Back from interface...")

    SK_CLIENT.close()

    logging.debug("signalk_client.Data closed...")

if __name__ == "__main__":
    main()
