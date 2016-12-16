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

"""pysk is an ncurses signalk client"""

import argparse
import curses
import json
import logging

# Global Variables
SK_CLIENT = None
STDSCR = None

class Page(object):
    """base class for a page in the ui
    """

    def __init__(self, max_y, max_x):
        self.max_y = max_y
        self.max_x = max_x
        self.pad = None
        self.pad_y = 0
        self.pad_off = 0

    @property
    def name(self):
        """return the page title - override me"""
        return "Unnamed Page"

    def update_pad_size(self, pad_y):
        """check pad size and update pad if neccesary"""
        if self.pad_y != pad_y:
            self.pad_y = pad_y
            self.pad = curses.newpad(self.pad_y, self.max_x)

    def term_resized(self, new_y, new_x):
        """handle terminal resize"""
        self.pad = curses.newpad(new_y, new_x)
        self.max_y = new_y
        self.max_x = new_x

    def refresh(self, start_y, start_x, stop_y, stop_x):
        """refresh the page"""
        self.pad.refresh(
            self.pad_off, 0,
            start_y, start_x,
            stop_y, stop_x)

    def command(self, char):
        """handle additional page specific commands"""
        if char == curses.KEY_LEFT or char == ord('h'):
            return ('VESSEL_BROWSER', None)
        return (None, None)


class VesselDetail(Page):
    """vessel detail page"""

    def __init__(self, max_y, max_x):
        Page.__init__(self, max_y, max_x)
        self.vessel = None
        self.update_pad_size(6)

    def set_vessel(self, vessel):
        """Set the Vessel to display detail for"""
        self.vessel = vessel

    @property
    def name(self):
        """return the page title"""
        return "Vessel Detail {}".format(self.vessel)

    def draw(self):
        """draw the page"""
        self.pad.erase()
        row = 0
        for key in ('name', 'mmsi', 'uuid', 'url', 'port', 'flag'):
            data = None
            try:
                data = self.vessel.get_datum(key)
            except KeyError:
                pass
            if data != None:
                self.pad.addstr(row, 0, "{}: {}".format(key, data.display_value()))
                row += 1


class TargetDetail(Page):
    """target detail page"""

    def __init__(self, max_y, max_x):
        Page.__init__(self, max_y, max_x)
        self.vessel = None
        self.path = None

    def set_target(self, vessel, path):
        """Set the Vessel and path of property to display detail for"""
        self.vessel = vessel
        self.path = path

    @property
    def name(self):
        """return the page title"""
        return "Target Detail {}.{}".format(str(self.vessel), self.path)

    def draw(self):
        """draw the page"""
        meta = self.vessel.data.get_prop_meta(self.path)
        meta_pp = json.dumps(meta, indent=2, sort_keys=True)
        prop = self.vessel.get_prop(self.path)
        prop_pp = json.dumps(prop, indent=2, sort_keys=True)
        self.update_pad_size(
            4 + meta_pp.count('\n') + prop_pp.count('\n')
            )
        self.pad.erase()
        self.pad.addstr(0, 0, "meta={}".format(meta_pp))
        self.pad.addstr(meta_pp.count('\n')+2, 0, "prop={}".format(prop_pp))


class VesselBrowser(Page):
    """vessel browser page"""
    def __init__(self, max_y, max_x):
        self.row_index = []
        self.row_count = 0

        for vessel in sorted(SK_CLIENT.data.get_vessels()):
            self.row_index.append(('vessel', vessel))
            self.row_count += 1
            for target in vessel.get_targets():
                self.row_count += 1
                self.row_index.append(('target', vessel, target))

        Page.__init__(self, max_y, max_x)
        self.pad_pos = 0 # current selected position
        self.sel_attr = curses.A_REVERSE

    @property
    def name(self):
        """return the page title"""
        return "Vessel Browser"

    def term_resized(self, new_y, new_x):
        """handle terminal resize"""
        self.pad = curses.newpad(self.row_count, new_x)
        self.max_y = new_y
        self.max_x = new_x

    def draw(self):
        """draw to page"""
        self.update_pad_size(len(self.row_index))
        self.pad.erase()
        for row in range(0, len(self.row_index)):
            if row >= self.row_count:
                logging.error("Overflowed pad at row: {}".format(row))
                break
            if self.row_index[row][0] == 'vessel':
                vessel = self.row_index[row][1]
                self.pad.addstr(row, 0, str(vessel))
            elif self.row_index[row][0] == 'target':
                vessel = self.row_index[row][1]
                path = self.row_index[row][2]
                datum = vessel.get_datum(path)
                mid_x = self.max_x/2
                self.pad.addstr(row, 2, datum.display_path())
                self.pad.addstr(row, mid_x, datum.display_value(
                    convert_units=[
                        ('m', 'ft'),
                        ('m/s', 'kn'),
                        ('rad', 'deg'),
                        ('K', 'F'),
                        ]
                    ))
            else:
                logging.error(
                    "Unknown row in row_index: {!r}".format(self.row_index[row])
                    )

        self.pad.chgat(self.pad_pos, 0, self.sel_attr)

        # handle pad scrolling
        mid_y = self.max_y/2
        if self.row_count > self.max_y:

            if self.pad_pos < mid_y:
                self.pad_off = 0

            elif (self.pad_pos >= mid_y and
                  self.pad_pos <= self.row_count-mid_y):

                self.pad_off = self.pad_pos-mid_y

            else:
                self.pad_off = self.row_count-self.max_y

    def command(self, char):
        """handle page specific commands"""
        if char == curses.KEY_DOWN or char == ord('j'):
            if self.pad_pos < self.row_count-1:
                self.pad_pos += 1
        elif char == curses.KEY_UP or char == ord('k'):
            if self.pad_pos > 0:
                self.pad_pos -= 1
        elif char == curses.KEY_NPAGE or char == ord('J'):
            if self.pad_pos < self.row_count-((self.max_y)/2):
                self.pad_pos += (self.max_y)/2
            else:
                self.pad_pos = self.row_count-1
        elif char == curses.KEY_PPAGE or char == ord('K'):
            if self.pad_pos > ((self.max_y)/2):
                self.pad_pos -= (self.max_y)/2
            else:
                self.pad_pos = 0
        elif char == curses.KEY_RIGHT or char == ord('l'):
            if self.row_index[self.pad_pos][0] == 'vessel':
                vessel = self.row_index[self.pad_pos][1]
                return ('VESSEL_DETAIL', vessel)

            if self.row_index[self.pad_pos][0] == 'target':
                vessel = self.row_index[self.pad_pos][1]
                path = self.row_index[self.pad_pos][2]
                return ('TARGET_DETAIL', (vessel, path))
        return (None, None)

def interface_console():
    """console ui"""

    import time

    while True:

        logging.info("- MARK -")
        time.sleep(60)


def interface_curses(win):
    """curses ui"""

    # Initialize curses

    global STDSCR
    STDSCR = win
    curses.raw()
    curses.halfdelay(5)
    max_y, max_x = STDSCR.getmaxyx()
    logging.info("got terminal size (y, x) = ({}, {})".format(max_y, max_x))

    # setup curses text attributes
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLUE)
        hdr_attr = curses.A_BOLD | curses.color_pair(1)
    else:
        hdr_attr = curses.A_STANDOUT

    all_pads = []
    vessel_browser = VesselBrowser(max_y-3, max_x)
    vessel_detail = VesselDetail(max_y-3, max_x)
    target_detail = TargetDetail(max_y-3, max_x)
    all_pads.append(vessel_browser)
    all_pads.append(vessel_detail)
    all_pads.append(target_detail)
    current_pad = vessel_browser

    while True:

        logging.debug("in main loop")
        if curses.is_term_resized(max_y, max_x):
            max_y, max_x = STDSCR.getmaxyx()
            logging.info(
                "terminal resize to (y, x) = ({}, {})".format(max_y, max_x)
                )
            curses.resizeterm(max_y, max_x)
            for pad in all_pads:
                pad.term_resized(max_y, max_x)
        STDSCR.erase()

        # draw the pad
        current_pad.draw()

        # draw the header and status bar
        STDSCR.addstr(0, 0, "[pysk] {}".format(current_pad.name))
        STDSCR.chgat(0, 0, hdr_attr)
        STDSCR.addstr(max_y-2, 0, "---server: {}".format(SK_CLIENT.server))
        STDSCR.chgat(max_y-2, 0, hdr_attr)

        # flip
        STDSCR.refresh()
        current_pad.refresh(1, 0, max_y-3, max_x)
        STDSCR.move(max_y-1, 0)

        char = STDSCR.getch()
        if char == ord('q') or char == ord('x') or char == 27:
            # q, x, or ESC exit
            logging.info("Exiting due to keypress")
            return 0
        else:
            (action, args) = current_pad.command(char)
            if action == 'VESSEL_BROWSER':
                current_pad = vessel_browser
            elif action == 'VESSEL_DETAIL':
                vessel_detail.set_vessel(args)
                current_pad = vessel_detail
            elif action == 'TARGET_DETAIL':
                vessel = args[0]
                path = args[1]
                target_detail.set_target(vessel, path)
                current_pad = target_detail

def wind_widget(name, gauge_radius, font, angle, speed, convert_units=[]):
    """wind angle and speed widget"""

    import math
    from PIL import Image
    from PIL import ImageDraw

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


def interface_papirus():
    """papirus ui"""

    import os
    import time
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
    from datetime import datetime
    from papirus import Papirus

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
