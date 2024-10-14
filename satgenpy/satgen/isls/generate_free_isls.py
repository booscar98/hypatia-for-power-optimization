import itertools
from satgen.distance_tools import *


def generate_free_isls(output_filename_isls, satellites, max_range, epoch_str, date_str, idx_offset=0):
    list_isls = []

    t_proc = 1 * 10**-3
    # Iterate over all pairs of satellites
    for (idx_a, sat_a), (idx_b, sat_b) in itertools.combinations(enumerate(satellites), 2):
        # Calculate the distance between satellite pairs
        distance = distance_m_between_satellites(sat_a, sat_b, epoch_str, date_str) #/ 299792458.0 + t_proc

        # Check if the distance is within the maximum range
        if distance <= (max_range): #/ 299792458.0:
            # Add ISL between satellites within the maximum range
            list_isls.append((idx_offset + idx_a, idx_offset + idx_b))

    # Write ISLs to the output file
    with open(output_filename_isls, 'w+') as f:
        for (a, b) in list_isls:
            f.write(str(a) + " " + str(b) + "\n")

    return list_isls
