# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
#   pysk is a console client for SignalK
#   Copyright (C) 2016-2018  Philip J Freeman <elektron@halo.nu>
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

"""pysk is a signalk client"""

import argparse
import importlib
import logging
import sys

from signalk_client.client import Client

INTERFACE_PLUGINS = (
    'console',
    'curses',
    )

def call_interface_plugin(name, *args, **kwargs):
    plugin = importlib.import_module("pysk.interface_%s" % name)
    plugin.interface_main(*args, **kwargs)


def main():
    """main"""

    print """
pysk Copyright (C) 2016-2018  Philip J Freeman <elektron@halo.nu>
This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
are welcome to redistribute it under certain conditions.
"""

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
        help='ui interface type ({})'.format(", ".join(INTERFACE_PLUGINS)),
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

    sk_client = Client(args.server)


    if args.interface in INTERFACE_PLUGINS:
        logging.debug("loading interface plugin: {}...".format(args.interface))
        call_interface_plugin(args.interface, sk_client=sk_client)
    else:
        logging.error("unknown interface: {}".format(args.interface))

    logging.debug("Back from interface...")

    sk_client.close()

    logging.debug("signalk_client.Data closed...")

if __name__ == "__main__":
    main()
