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
import time

from espeak import espeak

def interface_main(*args, **kwargs):

    logging.info("in interface talker")

    # initialize
    min_delay_timeout = 10
    max_delay_timeout = 60

    espeak.set_voice('en-us')
    espeak.synth('Welcome to pysk. This program comes with ABSOLUTELY NO WARRANTY.')

    sk_client = kwargs['sk_client']
    modes = kwargs['modes']
    conversions = kwargs['conversions']

    vessel_self = sk_client.data.get_self()

    data = {
        'speed': {
            'navigation.speedOverGround': {
                'name': "Ground Speed",
                'last_value': None,
                'last_timestamp': 0.0,
                },
            'navigation.speedThroughWater': {
                'name': "Water Speed",
                'last_value': None,
                'last_timestamp': 0.0,
                },
            },
        'depth': {
            'environment.depth.belowTransducer': {
                'name': "Depth",
                'last_value': None,
                'last_timestamp': 0.0,
                },
            },
        }

    while True:

        now = time.time()
        messages = []

        for mode in data.keys():
            if 'all' in modes or mode in modes:
                for datum in data[mode].keys():
                    try:
                        d = vessel_self.get_datum(datum)
                        next_value = d.display_value(convert_units=conversions, abbreviate_units=False)
                    except:
                        next_value = "unknown"
                    if (now > data[mode][datum]['last_timestamp'] + min_delay_timeout and
                        (next_value != data[mode][datum]['last_value'] or
                         now > data[mode][datum]['last_timestamp'] + max_delay_timeout)
                       ):
                        messages.append("{}, {}".format(data[mode][datum]['name'], next_value))
                        data[mode][datum]['last_value'] = next_value
                        data[mode][datum]['last_timestamp'] = now

        for message in messages:
            logging.info("say message: {}".format(message))
            espeak.synth(message)
        time.sleep(.33)
