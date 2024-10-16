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

from satgen.distance_tools import *
from astropy import units as u
import math
import networkx as nx
import numpy as np
import os
from .algorithm_free_one_only_gs_relays import algorithm_free_one_only_gs_relays
from .algorithm_free_one_only_over_isls import algorithm_free_one_only_over_isls
from .algorithm_paired_many_only_over_isls import algorithm_paired_many_only_over_isls
from .algorithm_free_gs_one_sat_many_only_over_isls import algorithm_free_gs_one_sat_many_only_over_isls
from .algorithm_oscar import algorithm_oscar
from satgen.isls import *


def generate_dynamic_state(
        output_dynamic_state_dir,
        results_dir,
        epoch,
        simulation_end_time_ns,
        time_step_ns,
        offset_ns,
        satellites,
        ground_stations,
        list_isls,
        list_gsl_interfaces_info,
        max_gsl_length_m,
        max_isl_length_m,
        dynamic_state_algorithm,  # Options:
                                  # "algorithm_free_one_only_gs_relays"
                                  # "algorithm_free_one_only_over_isls"
                                  # "algorithm_paired_many_only_over_isls"
        src_gs_node_id,
        dst_gs_node_id,
        enable_verbose_logs
):
    if offset_ns % time_step_ns != 0:
        raise ValueError("Offset must be a multiple of time_step_ns")
    prev_output = None
    i = 0
    total_iterations = ((simulation_end_time_ns - offset_ns) / time_step_ns)
    for time_since_epoch_ns in range(offset_ns, simulation_end_time_ns, time_step_ns):
        if not enable_verbose_logs:
            if i % int(math.floor(total_iterations) / 10.0) == 0:
                print("Progress: calculating for T=%d (time step granularity is still %d ms)" % (
                    time_since_epoch_ns, time_step_ns / 1000000
                ))
            i += 1
        prev_output = generate_dynamic_state_at(
            output_dynamic_state_dir,
            results_dir,
            epoch,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            dynamic_state_algorithm,
            prev_output,
            src_gs_node_id,
            dst_gs_node_id,
            enable_verbose_logs
        )


def generate_dynamic_state_at(
        output_dynamic_state_dir,
        results_dir,
        epoch,
        time_since_epoch_ns,
        satellites,
        ground_stations,
        list_isls,
        list_gsl_interfaces_info,
        max_gsl_length_m,
        max_isl_length_m,
        dynamic_state_algorithm,
        prev_output,
        src_gs_node_id,
        dst_gs_node_id,
        enable_verbose_logs
):
    if enable_verbose_logs:
        print("FORWARDING STATE AT T = " + (str(time_since_epoch_ns))
              + "ns (= " + str(time_since_epoch_ns / 1e9) + " seconds)")

    #################################

    if enable_verbose_logs:
        print("\nBASIC INFORMATION")

    # Time
    time = epoch + time_since_epoch_ns * u.ns
    if enable_verbose_logs:
        print("  > Epoch.................. " + str(epoch))
        print("  > Time since epoch....... " + str(time_since_epoch_ns) + " ns")
        print("  > Absolute time.......... " + str(time))

    temp_path = os.path.abspath(os.path.join(output_dynamic_state_dir, os.pardir))
    isls_dir = temp_path + "/ISLs/"
    list_isls = generate_free_isls(isls_dir + "isls_" + str(time_since_epoch_ns) + ".txt", satellites, max_isl_length_m, str(epoch), str(time), idx_offset=0)
    print("UPDATING ISLs")

    # Graphs
    sat_net_graph_only_satellites_with_isls = nx.Graph()
    sat_net_graph_all_with_only_gsls = nx.Graph()
    sat_net_graph_complete = nx.Graph()

    # Information
    for i in range(len(satellites)):
        sat_net_graph_only_satellites_with_isls.add_node(i)
        sat_net_graph_all_with_only_gsls.add_node(i)
    for i in range(len(satellites) + len(ground_stations)):
        sat_net_graph_all_with_only_gsls.add_node(i)
    for i in range(len(satellites) + len(ground_stations)):
        sat_net_graph_complete.add_node(i)
    if enable_verbose_logs:
        print("  > Satellites............. " + str(len(satellites)))
        print("  > Ground stations........ " + str(len(ground_stations)))
        print("  > Max. range GSL......... " + str(max_gsl_length_m) + "m")
        print("  > Max. range ISL......... " + str(max_isl_length_m) + "m")

    #################################

    if enable_verbose_logs:
        print("\nPrint SATELLITE INFORMATION")

    output_filename = output_dynamic_state_dir + "/Sat_Info_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename, "w+") as f_out:
        for s in range(len(satellites)):
            x, y, z = satellite_cartesian_coord(satellites[s], str(epoch), str(time))
            f_out.write("%d,%f,%f,%f\n" % (s, x, y, z))


    if enable_verbose_logs:
        print("\nISL INFORMATION")

    # ISL edges
    total_num_isls = 0
    num_isls_per_sat = [0] * len(satellites)
    sat_neighbor_to_if = {}
    output_filename_2 = output_dynamic_state_dir + "/ISLs_Info_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename_2, "w+") as f_out_2:
        for (a, b) in list_isls:

            # ISLs are not permitted to exceed their maximum distance
            # TODO: Technically, they can (could just be ignored by forwarding state calculation),
            # TODO: but practically, defining a permanent ISL between two satellites which
            # TODO: can go out of distance is generally unwanted
            sat_distance_m = distance_m_between_satellites(satellites[a], satellites[b], str(epoch), str(time))
            if sat_distance_m > max_isl_length_m:
                raise ValueError(
                    "The distance between two satellites (%d and %d) "
                    "with an ISL exceeded the maximum ISL length (%.2fm > %.2fm at t=%dns)"
                    % (a, b, sat_distance_m, max_isl_length_m, time_since_epoch_ns)
                )

            # Add to networkx graph
            sat_net_graph_only_satellites_with_isls.add_edge(
                a, b, weight=sat_distance_m
            )
            sat_net_graph_complete.add_edge(a, b, weight=sat_distance_m)
            # Interface mapping of ISLs
            sat_neighbor_to_if[(a, b)] = num_isls_per_sat[a]
            sat_neighbor_to_if[(b, a)] = num_isls_per_sat[b]
            num_isls_per_sat[a] += 1
            num_isls_per_sat[b] += 1
            total_num_isls += 1

            f_out_2.write("%d,%d,%f\n" % (a, b, sat_distance_m))

    if enable_verbose_logs:
        print("  > Total ISLs............. " + str(len(list_isls)))
        print("  > Min. ISLs/satellite.... " + str(np.min(num_isls_per_sat)))
        print("  > Max. ISLs/satellite.... " + str(np.max(num_isls_per_sat)))

    #################################

    if enable_verbose_logs:
        print("\nGSL INTERFACE INFORMATION")

    satellite_gsl_if_count_list = list(map(
        lambda x: x["number_of_interfaces"],
        list_gsl_interfaces_info[0:len(satellites)]
    ))
    ground_station_gsl_if_count_list = list(map(
        lambda x: x["number_of_interfaces"],
        list_gsl_interfaces_info[len(satellites):(len(satellites) + len(ground_stations))]
    ))
    if enable_verbose_logs:
        print("  > Min. GSL IFs/satellite........ " + str(np.min(satellite_gsl_if_count_list)))
        print("  > Max. GSL IFs/satellite........ " + str(np.max(satellite_gsl_if_count_list)))
        print("  > Min. GSL IFs/ground station... " + str(np.min(ground_station_gsl_if_count_list)))
        print("  > Max. GSL IFs/ground_station... " + str(np.max(ground_station_gsl_if_count_list)))

    #################################

    if enable_verbose_logs:
        print("\nGSL IN-RANGE INFORMATION")

    # What satellites can a ground station see
    ground_station_satellites_in_range = []
    output_filename_3 = output_dynamic_state_dir + "/GSLs_Info_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename_3, "w+") as f_out_3:
        for ground_station in ground_stations:
            # Find satellites in range
            satellites_in_range = []
            for sid in range(len(satellites)):
                distance_m = distance_m_ground_station_to_satellite(
                    ground_station,
                    satellites[sid],
                    str(epoch),
                    str(time)
                )
                if distance_m <= max_gsl_length_m:
                    satellites_in_range.append((distance_m, sid))
                    sat_net_graph_all_with_only_gsls.add_edge(
                        sid, len(satellites) + ground_station["gid"], weight=distance_m
                    )
                    f_out_3.write("%d,%d,%f\n" % (len(satellites) + ground_station["gid"], sid, distance_m))

                    sat_net_graph_complete.add_edge(sid, len(satellites) + ground_station["gid"], weight=distance_m)
            #print(sat_net_graph_all_with_only_gsls.number_of_nodes())
            #print(sat_net_graph_complete.number_of_nodes())
            ground_station_satellites_in_range.append(satellites_in_range)

    # Print how many are in range
    ground_station_num_in_range = list(map(lambda x: len(x), ground_station_satellites_in_range))
    if enable_verbose_logs:
        print("  > Min. satellites in range... " + str(np.min(ground_station_num_in_range)))
        print("  > Max. satellites in range... " + str(np.max(ground_station_num_in_range)))

    #################################

    #
    # Call the dynamic state algorithm which:
    #
    # (a) Output the gsl_if_bandwidth_<t>.txt files
    # (b) Output the fstate_<t>.txt files
    #
    if dynamic_state_algorithm == "algorithm_free_one_only_over_isls":

        return algorithm_free_one_only_over_isls(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            sat_neighbor_to_if,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )

    elif dynamic_state_algorithm == "algorithm_free_gs_one_sat_many_only_over_isls":

        return algorithm_free_gs_one_sat_many_only_over_isls(
            output_dynamic_state_dir,
            results_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            sat_neighbor_to_if,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )
    
    elif dynamic_state_algorithm == "algorithm_free_one_only_gs_relays":

        return algorithm_free_one_only_gs_relays(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_all_with_only_gsls,
            num_isls_per_sat,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )
    
    elif dynamic_state_algorithm == "algorithm_paired_many_only_over_isls":

        return algorithm_paired_many_only_over_isls(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            sat_neighbor_to_if,
            list_gsl_interfaces_info,
            prev_output,
            enable_verbose_logs
        )
    elif dynamic_state_algorithm == "algorithm_oscar":

        return algorithm_oscar(
            output_dynamic_state_dir,
            results_dir,
            time_since_epoch_ns,
            satellites,
            ground_stations,
            sat_net_graph_complete,
            sat_net_graph_only_satellites_with_isls,
            ground_station_satellites_in_range,
            num_isls_per_sat,
            list_gsl_interfaces_info,
            sat_neighbor_to_if,
            prev_output,
            src_gs_node_id,
            dst_gs_node_id,
            enable_verbose_logs
        )

    else:
        raise ValueError("Unknown dynamic state algorithm: " + str(dynamic_state_algorithm))
