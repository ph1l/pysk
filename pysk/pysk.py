# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
#   python-signalk-client is a python client library for SignalK
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

class VesselDetail(object):
    """vessel detail page"""

    def __init__(self, max_y, max_x):
        self.max_y = max_y
        self.max_x = max_x
        self.vessel = None
        self.pad = curses.newpad(self.max_y, self.max_x)

    def set_vessel(self, vessel):
        """Set the Vessel to display detail for"""
        self.vessel = vessel

    @property
    def name(self):
        """return the page title"""
        return "Vessel Detail {}".format(self.vessel)

    def term_resized(self, new_y, new_x):
        """handle terminal resize"""
        self.pad = curses.newpad(new_y, new_x)
        self.max_y = new_y
        self.max_x = new_x

    def draw(self):
        """draw the page"""
        self.pad.erase()
        row = 0
        for key in ('mmsi', 'url', 'uuid', 'name', 'port', 'flag'):
            data = ''
            try:
                data = SK_CLIENT.data.get_vessel_prop(key, self.vessel)
            except KeyError:
                pass
            self.pad.addstr(row, 0, "{}: {}".format(key, data))
            row += 1

    def refresh(self, start_y, start_x, stop_y, stop_x):
        """refresh the page"""
        self.pad.refresh(
            0, 0,
            start_y, start_x,
            stop_y, stop_x)

    def command(self, char):
        """handle additiona page specific commands"""
        if char == curses.KEY_LEFT or char == ord('h'):
            return ('VESSEL_BROWSER', None)
        return (None, None)

class TargetDetail(object):
    """target detail page"""

    def __init__(self, max_y, max_x):
        self.max_y = max_y
        self.max_x = max_x
        self.vessel = None
        self.path = None
        self.pad = curses.newpad(self.max_y, self.max_x)

    def set_target(self, vessel, path):
        """Set the Vessel and path of property to display detail for"""
        self.vessel = vessel
        self.path = path

    @property
    def name(self):
        """return the page title"""
        return "Target Detail {}.{}".format(self.vessel, self.path)

    def term_resized(self, new_y, new_x):
        """handle terminal resize"""
        self.pad = curses.newpad(new_y, new_x)
        self.max_y = new_y
        self.max_x = new_x

    def draw(self):
        """draw the page"""
        self.pad.erase()
        meta = SK_CLIENT.data.get_prop_meta(self.path)
        meta_pp = json.dumps(meta, indent=2, sort_keys=True)
        self.pad.addstr(0, 0, "meta={}".format(meta_pp))
        prop = SK_CLIENT.data.get_vessel_prop(self.path, self.vessel)
        prop_pp = json.dumps(prop, indent=2, sort_keys=True)
        self.pad.addstr(meta_pp.count('\n')+2, 0, "prop={}".format(prop_pp))

    def refresh(self, start_y, start_x, stop_y, stop_x):
        """refresh the page"""
        self.pad.refresh(
            0, 0,
            start_y, start_x,
            stop_y, stop_x)

    def command(self, char):
        """handle additional page specific commands"""
        if char == curses.KEY_LEFT or char == ord('h'):
            return ('VESSEL_BROWSER', None)
        return (None, None)

class VesselBrowser(object):
    """vessel browser page"""
    def __init__(self, max_y, max_x):
        self.max_y = max_y
        self.max_x = max_x
        self.row_index = []
        self.row_count = 0

        for vessel in sorted(SK_CLIENT.data.get_vessels()):
            self.row_index.append(('vessel', vessel))
            self.row_count += 1
            for target in sorted(SK_CLIENT.data.get_targets(vessel)):
                self.row_count += 1
                self.row_index.append(('target', vessel, target))
        self.display_pad = curses.newpad(self.row_count, self.max_x)
        self.display_pad_pos = 0 # current selected position
        self.display_pad_off = 0 # current display offset
        self.sel_attr = curses.A_REVERSE

    @property
    def name(self):
        """return the page title"""
        return "Vessel Browser"

    def term_resized(self, new_y, new_x):
        """handle terminal resize"""
        self.display_pad = curses.newpad(self.row_count, new_x)
        self.max_y = new_y
        self.max_x = new_x

    def draw(self):
        """draw to page"""
        self.display_pad.erase()
        for row in range(0, len(self.row_index)):
            if row >= self.row_count:
                logging.error("Overflowed display_pad at row: {}".format(row))
                break
            if self.row_index[row][0] == 'vessel':
                vessel = self.row_index[row][1]
                self.display_pad.addstr(row, 0, "vessel: {}".format(vessel))
            elif self.row_index[row][0] == 'target':
                vessel = self.row_index[row][1]
                path = self.row_index[row][2]
                datum = SK_CLIENT.data.get_vessel_prop_datum(path, vessel)
                mid_x = self.max_x/2
                self.display_pad.addstr(row, 2, datum.display_path())
                self.display_pad.addstr(row, mid_x, datum.display_value(
                    convert_units=[
                        ('m', 'ft'),
                        ('m/s', 'kn'),
                        ('rad', 'deg'),
                        ]
                    ))
            else:
                logging.error(
                    "Unknown row in row_index: {!r}".format(self.row_index[row])
                    )

        self.display_pad.chgat(self.display_pad_pos, 0, self.sel_attr)

        # handle pad scrolling
        mid_y = self.max_y/2
        if self.row_count > self.max_y:

            if self.display_pad_pos < mid_y:
                self.display_pad_off = 0

            elif (self.display_pad_pos >= mid_y and
                  self.display_pad_pos <= self.row_count-mid_y):

                self.display_pad_off = self.display_pad_pos-mid_y

            else:
                self.display_pad_off = self.row_count-self.max_y

    def refresh(self, start_y, start_x, stop_y, stop_x):
        """refresh the page"""
        self.display_pad.refresh(
            self.display_pad_off, 0,
            start_y, start_x,
            stop_y, stop_x)

    def command(self, char):
        """handle page specific commands"""
        if char == curses.KEY_DOWN or char == ord('j'):
            if self.display_pad_pos < self.row_count-1:
                self.display_pad_pos += 1
        elif char == curses.KEY_UP or char == ord('k'):
            if self.display_pad_pos > 0:
                self.display_pad_pos -= 1
        elif char == curses.KEY_NPAGE or char == ord('J'):
            if self.display_pad_pos < self.row_count-((self.max_y)/2):
                self.display_pad_pos += (self.max_y)/2
            else:
                self.display_pad_pos = self.row_count-1
        elif char == curses.KEY_PPAGE or char == ord('K'):
            if self.display_pad_pos > ((self.max_y)/2):
                self.display_pad_pos -= (self.max_y)/2
            else:
                self.display_pad_pos = 0
        elif char == curses.KEY_RIGHT or char == ord('l'):
            if self.row_index[self.display_pad_pos][0] == 'vessel':
                vessel = self.row_index[self.display_pad_pos][1]
                return ('VESSEL_DETAIL', vessel)

            if self.row_index[self.display_pad_pos][0] == 'target':
                vessel = self.row_index[self.display_pad_pos][1]
                path = self.row_index[self.display_pad_pos][2]
                return ('TARGET_DETAIL', (vessel, path))
        return (None, None)


def interface_curses(win):
    """main ui function for pysk"""

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

    logging.debug("Going curses...")

    curses.wrapper(interface_curses)

    logging.debug("Back from curses...")

    SK_CLIENT.close()

    logging.debug("signalk_client.Data closed...")

if __name__ == "__main__":
    main()
