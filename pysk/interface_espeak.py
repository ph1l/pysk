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

    SK_CLIENT = kwargs['sk_client']
    vessel_self = SK_CLIENT.data.get_self()

    last_speedOverGround_value = None
    last_speedOverGround_timestamp = 0.0
    last_speedThroughWater_value = None
    last_speedThroughWater_timestamp = 0.0
    last_depth_value = None
    last_depth_timestamp = 0.0

    while True:

        now = time.time()
        messages = []

        # speedOverGround
        try:
            speedOverGround = vessel_self.get_datum('navigation.speedOverGround')
        except:
            speedOverGround = None

        next_speedOverGround_value = "{:.1f}".format(speedOverGround.value)
        if (
            speedOverGround != None and
            now > last_speedOverGround_timestamp + min_delay_timeout and
            (
                next_speedOverGround_value != last_speedOverGround_value or
                now > last_speedOverGround_timestamp + max_delay_timeout
            )
           ):
            messages.append("Ground Speed, {}".format(next_speedOverGround_value))
            last_speedOverGround_value = next_speedOverGround_value
            last_speedOverGround_timestamp = now

        # speedThroughWater
        try:
            speedThroughWater = vessel_self.get_datum('navigation.speedThroughWater')
        except:
            speedThroughWater = None

        next_speedThroughWater_value = "{:.1f}".format(speedThroughWater.value)
        if (
            speedThroughWater != None and
            now > last_speedThroughWater_timestamp + min_delay_timeout and
            (
                next_speedThroughWater_value != last_speedThroughWater_value or
                now > last_speedThroughWater_timestamp + max_delay_timeout
            )
           ):
            messages.append("Water Speed, {}".format(next_speedThroughWater_value))
            last_speedThroughWater_value = next_speedThroughWater_value
            last_speedThroughWater_timestamp = now

        # depth.belowTransducer
        try:
            depth = vessel_self.get_datum('environment.depth.belowTransducer')
        except:
            depth = None

        next_depth_value = "{:.1f}".format(depth.value)
        if (
            depth != None and
            now > last_depth_timestamp + min_delay_timeout and
            (
                next_depth_value != last_depth_value or
                now > last_depth_timestamp + max_delay_timeout
            )
           ):
            messages.append("Depth, {}".format(next_depth_value))
            last_depth_value = next_depth_value
            last_depth_timestamp = now

        for message in messages:
            logging.info("say message: {}".format(message))
            espeak.synth(message)
        time.sleep(.33)
