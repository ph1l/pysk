# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
#
#   pysk is a ncurses client for SignalK
#   Copyright (C) 2017-2018  Philip J Freeman <elektron@halo.nu>
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
import time

def interface_main(*args, **kwargs):
    """console ui"""

    logging.error("This is a dummy interface. Possibly useful with an increased logging level.")

    signalk = kwargs['sk_client']

    vessels = signalk.data.get_vessels()
    targets = {}
    for v in vessels:
        targets[v.key] = v.get_targets()

    while True:

        for v in vessels:
            logging.info("Vessel: {}".format(v.key))
            for t in targets[v.key]:
                value = v.get_prop(t)
                logging.info("  Target: {} = {}".format(t, value))
            time.sleep(1)

