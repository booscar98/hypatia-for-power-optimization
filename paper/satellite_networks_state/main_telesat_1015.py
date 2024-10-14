# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import math
from main_helper import MainHelper

# WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
EARTH_RADIUS = 6378135.0

# GENERATION CONSTANTS

BASE_NAME = "telesat_1015"
NICE_NAME = "Telesat-1015"

# KUIPER 630

ECCENTRICITY = 0.0000001  # Circular orbits are zero, but pyephem does not permit 0, so lowest possible value
ARG_OF_PERIGEE_DEGREE = 0.0
PHASE_DIFF = True

################################################################
# The below constants are taken from Telesat's FCC filing as below:
# [1]: https://fcc.report/IBFS/SAT-MPL-20200526-00053/2378318.pdf
################################################################

MEAN_MOTION_REV_PER_DAY = 13.66  # Altitude ~1015 km
ALTITUDE_M = 1015000  # Altitude ~1015 km
SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(10.0))  # Considering an elevation angle of 10 degrees;
MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))
# ISLs are not allowed to dip below 80 km altitude in order to avoid weather conditions
MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))
NUM_ORBS = 27
NUM_SATS_PER_ORB = 13
INCLINATION_DEGREE = 98.98

################################################################

main_helper = MainHelper(
        BASE_NAME,
        NICE_NAME,
        ECCENTRICITY,
        ARG_OF_PERIGEE_DEGREE,
        PHASE_DIFF,
        MEAN_MOTION_REV_PER_DAY,
        ALTITUDE_M,
        MAX_GSL_LENGTH_M,
        MAX_ISL_LENGTH_M,
        NUM_ORBS,
        NUM_SATS_PER_ORB,
        INCLINATION_DEGREE,
)


def main():
    args = sys.argv[1:]
    if len(args) != 8:
        print("Must supply exactly six arguments")
        print("Usage: python main_telesat_1015.py [duration (s)] [time step (ms)] "
              "[isls_plus_grid / isls_none] "
              "[ground_stations_{top_100, paris_moscow_grid, generated_1000}] "
              "[algorithm_{free_one_only_over_isls, free_one_only_gs_relays, paired_many_only_over_isls, oscar}] "
              "[num threads]")
        exit(1)
    else:
        main_helper.calculate(
            "gen_data",
            int(args[0]),
            int(args[1]),
            args[2],
            args[3],
            args[4],
            int(args[5]),
            int(args[6]),
            int(args[7]),
        )


if __name__ == "__main__":
    main()
