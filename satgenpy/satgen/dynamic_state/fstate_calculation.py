import math
import networkx as nx
import numpy as np
import os

"""
def calculate_fstate_shortest_path_without_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):
    # Constant transmission time in seconds

    # Update edge weights to include transmission time + processing time
    for edge in sat_net_graph_only_satellites_with_isls.edges(data=True):
        edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)

    # Perform shortest path calculation
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)
    output_filename_test = output_dynamic_state_dir + "dist_sat_net_without_gs_fstate_" + str(time_since_epoch_ns) + ".txt"
    np.savetxt(output_filename_test, dist_sat_net_without_gs, delimiter=',')
    # Forwarding state
    fstate = {}


    #Global optimazer helper
    total_power_global = 1000000000000000
    src_gs_node_id = 0
    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    #while src_gs_node_id < num_satellites + num_ground_stations:
    with open(output_filename, "w+") as f_out:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        output_filename_test = output_dynamic_state_dir + "possibilities_" + str(time_since_epoch_ns) + ".txt"
        with open(output_filename_test, "w+") as f_out_2:
            dist_satellite_to_ground_station = {}
            for curr in range(num_satellites):
                output_filename_test = output_dynamic_state_dir + "_dist_any_sat_any_gs_TOT_" + str(time_since_epoch_ns) + ".txt"
                with open(output_filename_test, "w+") as f_out_3:
                    for dst_gid in range(num_ground_stations):
                        dst_gs_node_id = num_satellites + dst_gid

                        # Among the satellites in range of the destination ground station,
                        # find the one which promises the shortest distance
                        possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
                        possibilities = []
                        for b in possible_dst_sats:
                            if not math.isinf(dist_sat_net_without_gs[(curr, b[1])]):  # Must be reachable
                                pow = math.log10(b[0] / 1000)
                                possibilities.append(
                                    (
                                        dist_sat_net_without_gs[(curr, b[1])] + pow,
                                        b[1]
                                    )
                                )
                        
                        for i in range(len(possibilities)):
                            distance_value = possibilities[i][0]
                            # Calculate the logarithm of the distance value
                            log_distance_value = math.log10(distance_value)
                            # Update the first element of the tuple with the logarithm value
                            possibilities[i] = (log_distance_value, possibilities[i][1])
                          
                        possibilities = list(sorted(possibilities))
                        #for possibility in possibilities:
                        #    f_out_2.write(f"{curr}, {dst_gs_node_id}, {possibility[0]}, {possibility[1]}\n")


                    # By default, if there is no satellite in range for the
                    # destination ground station, it will be dropped (indicated by -1)
                    next_hop_decision = (-1, -1, -1)
                    distance_to_ground_station_m = float("inf")
                    if len(possibilities) > 0:
                        dst_sat = possibilities[0][1]
                        distance_to_ground_station_m = possibilities[0][0]
                        #possibilities[1][0] = math.log10(possibilities[1][0])

                        # If the current node is not that satellite, determine how to get to the satellite
                        if curr != dst_sat:

                            # Among its neighbors, find the one which promises the
                            # lowest distance to reach the destination satellite
                            best_distance_m = 1000000000000000
                            for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                                distance_m = (
                                        sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                                        +
                                        dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                                )
                                if distance_m < best_distance_m:
                                    next_hop_decision = (
                                        neighbor_id,
                                        sat_neighbor_to_if[(curr, neighbor_id)],
                                        sat_neighbor_to_if[(neighbor_id, curr)]
                                    )
                                    best_distance_m = distance_m

                        else:
                            # This is the destination satellite, as such the next hop is the ground station itself
                            next_hop_decision = (
                                dst_gs_node_id,
                                num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                                0
                            )

                    # In any case, save the distance of the satellite to the ground station to re-use
                    # when we calculate ground station to ground station forwarding
                    dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = distance_to_ground_station_m
                    
                    #Debugging
                    f_out_2.write("%d,%d,%f\n" % (
                        curr,
                        dst_gs_node_id,
                        distance_to_ground_station_m
                    ))
                    
                    # Write to forwarding state
                    if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            curr,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(curr, dst_gs_node_id)] = next_hop_decision
                #print("Dest Sat: ", possibilities[0])
                #print(len(possibilities))

        # Ground stations to ground stations
        # Choose the source satellite which promises the shortest path
        #output_filename_test = output_dynamic_state_dir + "_dist_any_sat_any_gs_TOT_" + str(time_since_epoch_ns) + ".txt"
        #with open(output_filename_test, "w+") as f_out_3:
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid

                    # Among the satellites in range of the source ground station,
                    # find the one which promises the shortest distance
                    possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
                    possibilities = []
                    for a in possible_src_sats:
                        best_distance_offered_m = dist_satellite_to_ground_station[(a[1], dst_gs_node_id)]
                        if not math.isinf(best_distance_offered_m):
                            pow = math.log10(a[0] / 1000)
                            #print("pow: ", pow)
                            possibilities.append(
                                (
                                    pow + best_distance_offered_m,
                                    a[1]
                                )
                            )
                    possibilities = list(sorted(possibilities))
                    # By default, if there is no satellite in range for one of the
                    # ground stations, it will be dropped (indicated by -1)
                    next_hop_decision = (-1, -1, -1)
                    if len(possibilities) > 0:
                        src_sat_id = possibilities[0][1]
                        next_hop_decision = (
                            src_sat_id,
                            0,
                            num_isls_per_sat[src_sat_id] + gid_to_sat_gsl_if_idx[src_gid]
                        )

                    # Update forwarding state
                    if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            src_gs_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision
                    total_power = possibilities[0][0]
    
                    
                    #Debugging
                    f_out_3.write("%d,%d,%d,%f\n" % (
                        possibilities[0][1],
                        src_gid + num_satellites,
                        dst_gid + num_satellites,
                        possibilities[0][0]
                    ))
                    
                #print("Source Sat: ", possibilities[0])
                #print(len(possibilities))
                #print("Possible src sats: ", possible_src_sats)
                #print("Best Dist Offered m: ", best_distance_offered_m)
                #print("pow: ", pow)

        print(src_gs_node_id)
        if total_power < total_power_global:
            print("I Enter if")
            #Clear old fstate.txt file and copy the new fstate file
            output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
            with open(output_filename, "w") as f:
                f.write("")  # Clearing the file
            with open(output_filename, "w+") as f:
                for key, value in fstate.items():
                    f.write("%s,%s,%s,%s,%s\n" % (key[0], key[1], value[0], value[1], value[2]))
            fstate_global = fstate
            total_power_global = total_power
        src_gs_node_id +=1

        
    # Finally return result
    return fstate
"""


def calculate_fstate_shortest_path_without_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):
    # Update edge weights to include transmission time + processing time
    for edge in sat_net_graph_only_satellites_with_isls.edges(data=True):
        edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)

    # Perform shortest path calculation
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        dist_satellite_to_ground_station = {}
        dist_to_gs_m_test_dic = {}
        for curr in range(num_satellites):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Among the satellites in range of the destination ground station,
                # find the one which promises the shortest distance
                possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
                possibilities = []
                for b in possible_dst_sats:
                    if not math.isinf(dist_sat_net_without_gs[(curr, b[1])]):  # Must be reachable
                        power = math.log10(b[0] / 1000)
                        possibilities.append(
                            (
                                dist_sat_net_without_gs[(curr, b[1])] + b[0],
                                b[1]
                            )
                        )
                possibilities = list(sorted(possibilities))
                
                # By default, if there is no satellite in range for the
                # destination ground station, it will be dropped (indicated by -1)
                next_hop_decision = (-1, -1, -1)
                distance_to_ground_station_m = float("inf")
                dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = []
                for possibility in possibilities:
                    if len(possibilities) > 0:
                        dst_sat = possibility[1]
                        distance_to_ground_station_m = possibility[0]
                        #possibilities[1][0] = math.log10(possibilities[1][0])

                        # If the current node is not that satellite, determine how to get to the satellite
                        if curr != dst_sat:

                            # Among its neighbors, find the one which promises the
                            # lowest distance to reach the destination satellite
                            best_distance_m = 1000000000000000
                            dst_sat = int(dst_sat)
                            for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                                distance_m = (
                                        sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                                        +
                                        dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                                )
                                if distance_m < best_distance_m:
                                    next_hop_decision = (
                                        neighbor_id,
                                        sat_neighbor_to_if[(curr, neighbor_id)],
                                        sat_neighbor_to_if[(neighbor_id, curr)]
                                    )
                                    best_distance_m = distance_m

                        else:
                            # This is the destination satellite, as such the next hop is the ground station itself
                            next_hop_decision = (
                                dst_gs_node_id,
                                num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                                0
                            )

                        # In any case, save the distance of the satellite to the ground station to re-use
                        # when we calculate ground station to ground station forwarding
                        dist_satellite_to_ground_station[(curr, dst_gs_node_id)].append(distance_to_ground_station_m)

                        # Write to forwarding state
                if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                    f_out.write("%d,%d,%d,%d,%d\n" % (
                        curr,
                        dst_gs_node_id,
                        next_hop_decision[0],
                        next_hop_decision[1],
                        next_hop_decision[2]
                    ))
                fstate[(curr, dst_gs_node_id)] = next_hop_decision
        #print("Dest Sat: ", possible_dst_sats)
        # Ground stations to ground stations
        # Choose the source satellite which promises the shortest path
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid

                    # Among the satellites in range of the source ground station,
                    # find the one which promises the shortest distance
                    possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
                    possibilities = []
                    for a in possible_src_sats:
                        for distance in dist_satellite_to_ground_station[(a[1], dst_gs_node_id)]:
                            best_distance_offered_m = distance
                            if not math.isinf(best_distance_offered_m):
                                power = math.log10(a[0] / 1000)
                                possibilities.append(
                                    (
                                        power + best_distance_offered_m,
                                        a[1]
                                    )
                                )
                    possibilities = sorted(possibilities)

                    # By default, if there is no satellite in range for one of the
                    # ground stations, it will be dropped (indicated by -1)
                    next_hop_decision = (-1, -1, -1)
                    if len(possibilities) > 0:
                        src_sat_id = possibilities[0][1]
                        next_hop_decision = (
                            src_sat_id,
                            0,
                            num_isls_per_sat[src_sat_id] + gid_to_sat_gsl_if_idx[src_gid]
                        )

                    # Update forwarding state
                    if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            src_gs_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision

    # Finally return result
    return fstate


def calculate_fstate_shortest_path_with_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):

    # Calculate shortest paths
    if enable_verbose_logs:
        print("  > Calculating Floyd-Warshall for graph including ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_sat_net = nx.floyd_warshall_numpy(sat_net_graph)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites and ground stations to ground stations
        for current_node_id in range(num_satellites + num_ground_stations):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Cannot forward to itself
                if current_node_id != dst_gs_node_id:

                    # Among its neighbors, find the one which promises the
                    # lowest distance to reach the destination satellite
                    next_hop_decision = (-1, -1, -1)
                    best_distance_m = 1000000000000000
                    for neighbor_id in sat_net_graph.neighbors(current_node_id):

                        # Any neighbor must be reachable
                        if math.isinf(dist_sat_net[(current_node_id, neighbor_id)]):
                            raise ValueError("Neighbor cannot be unreachable")

                        # Calculate distance = next-hop + distance the next hop node promises
                        distance_m = (
                            sat_net_graph.edges[(current_node_id, neighbor_id)]["weight"]
                            +
                            dist_sat_net[(neighbor_id, dst_gs_node_id)]
                        )
                        if (
                                not math.isinf(dist_sat_net[(neighbor_id, dst_gs_node_id)])
                                and
                                distance_m < best_distance_m
                        ):

                            # Check node identifiers to determine what are the
                            # correct interface identifiers
                            if current_node_id >= num_satellites and neighbor_id < num_satellites:  # GS to sat.
                                my_if = 0
                                next_hop_if = (
                                    num_isls_per_sat[neighbor_id]
                                    +
                                    gid_to_sat_gsl_if_idx[current_node_id - num_satellites]
                                )

                            elif current_node_id < num_satellites and neighbor_id >= num_satellites:  # Sat. to GS
                                my_if = (
                                    num_isls_per_sat[current_node_id]
                                    +
                                    gid_to_sat_gsl_if_idx[neighbor_id - num_satellites]
                                )
                                next_hop_if = 0

                            elif current_node_id < num_satellites and neighbor_id < num_satellites:  # Sat. to sat.
                                my_if = sat_neighbor_to_if[(current_node_id, neighbor_id)]
                                next_hop_if = sat_neighbor_to_if[(neighbor_id, current_node_id)]

                            else:  # GS to GS
                                raise ValueError("GS-to-GS link cannot exist")

                            # Write the next-hop decision
                            next_hop_decision = (
                                neighbor_id,  # Next-hop node identifier
                                my_if,        # My outgoing interface id
                                next_hop_if   # Next-hop incoming interface id
                            )

                            # Update best distance found
                            best_distance_m = distance_m

                    # Write to forwarding state
                    if not prev_fstate or prev_fstate[(current_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            current_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(current_node_id, dst_gs_node_id)] = next_hop_decision

    # Finally return result
    return fstate


def calculate_global_optimal_path(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):
    # Constant transmission time in seconds

    # Update edge weights to include transmission time + processing time
    for edge in sat_net_graph_only_satellites_with_isls.edges(data=True):
        edge[2]['weight'] = math.log10(edge[2]['weight'])

    # Perform shortest path calculation
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Ground stations to ground stations
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid

                    # Find the optimal path between source and destination ground stations
                    optimal_path = find_optimal_path(src_gs_node_id, dst_gs_node_id, sat_net_graph_only_satellites_with_isls,
                                                      dist_sat_net_without_gs, ground_station_satellites_in_range_candidates,
                                                      num_isls_per_sat, gid_to_sat_gsl_if_idx)

                    # Update forwarding state
                    if not prev_fstate or prev_fstate.get((src_gs_node_id, dst_gs_node_id)) != optimal_path:
                        f_out.write(f"{src_gs_node_id},{dst_gs_node_id},{optimal_path[0]},{optimal_path[1]},{optimal_path[2]}\n")
                    fstate[(src_gs_node_id, dst_gs_node_id)] = optimal_path

    # Finally return result
    return fstate


def find_optimal_path(src_node, dst_node, sat_net_graph, dist_sat_net_without_gs, ground_station_satellites_in_range_candidates,
                      num_isls_per_sat, gid_to_sat_gsl_if_idx):
    # Find the optimal path between source and destination ground stations
    optimal_path = None
    min_distance = float('inf')

    # Consider all possible satellite hops
    for sat in range(len(sat_net_graph)):
        # Calculate the distance from source to destination via the current satellite
        distance = dist_sat_net_without_gs[(src_node, sat)] + dist_sat_net_without_gs[(sat, dst_node)]

        if distance < min_distance:
            min_distance = distance
            next_hop_decision = (sat, num_isls_per_sat[sat] + gid_to_sat_gsl_if_idx[dst_node - len(sat_net_graph)], 0)

    return next_hop_decision

"""
def calculate_fstate_shortest_path_oscar(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_complete,
        sat_net_graph_only_satellites_with_isls,
        ground_station_satellites_in_range_candidates,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):
    
    #print(num_satellites)
    for edge in sat_net_graph_complete.edges(data=True):
        edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)

    for edge in sat_net_graph_only_satellites_with_isls.edges(data=True):
        edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)

    # Perform shortest path calculation global graph 
    dist_sat_net_complete = nx.floyd_warshall_numpy(sat_net_graph_complete)
    # Perform shortest path calculation between satellites
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)
    # Forwarding state
    fstate = {}
    output_filename_test = output_dynamic_state_dir + "Shortest_dists_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename_test, "w+") as f_out_2:
        for src_gid in range(num_ground_stations):
                for dst_gid in range(num_ground_stations):
                    if src_gid != dst_gid:
                        src_gs_node_id = num_satellites + src_gid
                        dst_gs_node_id = num_satellites + dst_gid
                        edge_weight = dist_sat_net_complete[(src_gs_node_id, dst_gs_node_id)]
                        f_out_2.write(f"src_gs_node_id: {src_gs_node_id}, dst_gs_node_id: {dst_gs_node_id}, edge_weight: {edge_weight}\n")

    # Now, find src_sat and dst_satthat promise the shortest path
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename, "w+") as f_out:
        best_src_dst_sats = {}
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid
                    #print(ground_station_satellites_in_range_candidates)
                    #print(dst_gid)
                    possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
                    #print(possible_src_sats)
                    possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
                    #print(possible_dst_sats)
                    for a in possible_src_sats:
                        #a = satellite_info[1]
                        dist_sat_src_gs = sat_net_graph_complete.edges[(a[1], src_gs_node_id)]["weight"]
                        for b in possible_dst_sats:
                            dist_sat_dst_gs = sat_net_graph_complete.edges[(b[1], dst_gs_node_id)]["weight"]
                            dist_isl = dist_sat_net_without_gs[(a[1], b[1])]
                            dist_total = dist_sat_src_gs + dist_sat_dst_gs + dist_isl
                            #print("SRC: ", src_gs_node_id)
                            #print("SRC: ", dst_gs_node_id)
                            print("Total Dist: ", dist_total)
                            #print("Dist SAt Net Complete: ", dist_sat_net_complete[(src_gs_node_id, dst_gs_node_id)])
                            if dist_total == dist_sat_net_complete[(src_gs_node_id, dst_gs_node_id)]:
                                src_sat = a[1]
                                dst_sat = b[1]
                                best_src_dst_sats = {
                                    'dst_gs_node_id': dst_gs_node_id,
                                    'src_gs_node_id': src_gs_node_id,
                                    'src_sat': src_sat,
                                    'dst_sat': dst_sat
                                }
    #return best_src_dst_sats

                                #f_out_2.write(f"src_gs_node_id: {src_gs_node_id}, dst_gs_node_id: {dst_gs_node_id}, src_sat: {src_sat}, dst_sat: {dst_sat}\n")
                                dist_satellite_to_ground_station = {}
                                for curr in range(num_satellites):
                                    next_hop_decision = (-1, -1, -1)
                                    distance_to_ground_station_m = float("inf")
                                    dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = []
                                    # If the current node is not that satellite, determine how to get to the satellite
                                    if curr != dst_sat:

                                        # Among its neighbors, find the one which promises the
                                        # lowest distance to reach the destination satellite
                                        best_distance_m = 1000000000000000
                                        #dst_sat = int(dst_sat)
                                        for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                                            distance_m = (
                                                sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                                                +
                                                dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                                            )
                                            if distance_m < best_distance_m:
                                                next_hop_decision = (
                                                    neighbor_id,
                                                    sat_neighbor_to_if[(curr, neighbor_id)],
                                                    sat_neighbor_to_if[(neighbor_id, curr)]
                                                )
                                            best_distance_m = distance_m

                                    else:
                                        # This is the destination satellite, as such the next hop is the ground station itself
                                        #print(num_isls_per_sat[dst_sat])
                                        #print(gid_to_sat_gsl_if_idx[dst_gs_node_id])
                                        next_hop_decision = (
                                            dst_gs_node_id,
                                            num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                                            0
                                        )

                                    # In any case, save the distance of the satellite to the ground station to re-use
                                    # when we calculate ground station to ground station forwarding
                                    dist_satellite_to_ground_station[(curr, dst_gs_node_id)].append(distance_to_ground_station_m)

                                    # Write to forwarding state
                                    if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                                        f_out.write("%d,%d,%d,%d,%d\n" % (
                                            curr,
                                            dst_gs_node_id,
                                            next_hop_decision[0],
                                            next_hop_decision[1],
                                            next_hop_decision[2]
                                        ))
                                    fstate[(curr, dst_gs_node_id)] = next_hop_decision
                                    print("Print fstate curr")
                                # Adding src_gs to the fstate
                                # By default, if there is no satellite in range for one of the
                                # ground stations, it will be dropped (indicated by -1)
                                next_hop_decision = (
                                    src_sat,
                                    0,
                                    num_isls_per_sat[src_sat] + gid_to_sat_gsl_if_idx[src_gid]
                                )

                                # Update forwarding state
                                if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
                                    f_out.write("%d,%d,%d,%d,%d\n" % (
                                        src_gs_node_id,
                                        dst_gs_node_id,
                                        next_hop_decision[0],
                                        next_hop_decision[1],
                                        next_hop_decision[2]
                                    ))
                                fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision
                                print("Final fstate")
                break
    return fstate
"""
"""
#THE GOOD ONE IS HERE
def calculate_fstate_shortest_path_oscar(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_complete,
        sat_net_graph_only_satellites_with_isls,
        ground_station_satellites_in_range_candidates,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        sat_neighbor_to_if,
        prev_fstate,
        src_gs_node_id,
        dst_gs_node_id,
        enable_verbose_logs
):
    
    print("SRC_gs: ", src_gs_node_id)
    print("DST_gs: ", dst_gs_node_id)
    for edge in sat_net_graph_complete.edges(data=True):
        edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)

    for edge in sat_net_graph_only_satellites_with_isls.edges(data=True):
        edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)

    # Perform shortest path calculation global graph 
    dist_sat_net_complete = nx.floyd_warshall_numpy(sat_net_graph_complete)
    # Perform shortest path calculation between satellites
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)
    
    output_filename_test = output_dynamic_state_dir + "Shortest_dists_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename_test, "w+") as f_out_2:
        for src_gid in range(num_ground_stations):
                for dst_gid in range(num_ground_stations):
                    if src_gid != dst_gid:
                        src_gs_node_id_temp = num_satellites + src_gid
                        dst_gs_node_id_temp = num_satellites + dst_gid
                        edge_weight = dist_sat_net_complete[(src_gs_node_id_temp, dst_gs_node_id_temp)]
                        f_out_2.write(f"src_gs_node_id: {src_gs_node_id_temp}, dst_gs_node_id: {dst_gs_node_id_temp}, edge_weight: {edge_weight}\n")

    # Now, find src_sat and dst_satthat promise the shortest path
    best_src_dst_sats_dic = {}
    if src_gs_node_id != dst_gs_node_id:
        #src_gs_node_id_temp = num_satellites + src_gid
        #dst_gs_node_id_temp = num_satellites + dst_gid
        src_gid = src_gs_node_id - num_satellites
        dst_gid = dst_gs_node_id - num_satellites
        #print(ground_station_satellites_in_range_candidates)
        #print(dst_gid)
        possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
        #print(possible_src_sats)
        possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
        #print(possible_dst_sats)
        src_sat = 0
        dst_sat = 0
        total_dist = 10000000000000
        for a in possible_src_sats:
            #a = satellite_info[1]
            dist_sat_src_gs = sat_net_graph_complete.edges[(a[1], src_gs_node_id)]["weight"]
            for b in possible_dst_sats:
                dist_sat_dst_gs = sat_net_graph_complete.edges[(b[1], dst_gs_node_id)]["weight"]
                dist_isl = dist_sat_net_without_gs[(a[1], b[1])]
                dist_total = dist_sat_src_gs + dist_sat_dst_gs + dist_isl
                #print("SRC: ", src_gs_node_id)
                #print("SRC: ", dst_gs_node_id)
                print("Total Dist: ", dist_total)
                print("Dist SAt Net Complete: ", dist_sat_net_complete[(src_gs_node_id, dst_gs_node_id)])
                if dist_total <= total_dist:
                    print("Enter IF")
                    src_sat = a[1]
                    dst_sat = b[1]
                    total_dist = dist_total
                    best_src_dst_sats_dic = {
                        'src_gs_node_id': src_gs_node_id,
                        'dst_gs_node_id': dst_gs_node_id,
                        'src_sat': src_sat,
                        'dst_sat': dst_sat
                    }
    print(src_sat)
    print(dst_sat)
    print(total_dist)
    # Forwarding state
    fstate = {}
    output_filename = output_dynamic_state_dir + "/fstate_" + str(src_gs_node_id) + "_to_" + str(dst_gs_node_id) + "_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename, "w+") as f_out:
    #return best_src_dst_sats
        #src_sat = best_src_dst_sats_dic['src_sat']
        #dst_sat = best_src_dst_sats_dic['dst_sat']
        #src_sat, dst_sat = best_src_dst_sats_dic.get((src_gs_node_id, dst_gs_node_id), None)
        #f_out_2.write(f"src_gs_node_id: {src_gs_node_id}, dst_gs_node_id: {dst_gs_node_id}, src_sat: {src_sat}, dst_sat: {dst_sat}\n")
        dist_satellite_to_ground_station = {}
        for curr in range(num_satellites):
            next_hop_decision = (-1, -1, -1)
            distance_to_ground_station_m = float("inf")
            dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = []
            # If the current node is not that satellite, determine how to get to the satellite
            if curr != dst_sat:

                # Among its neighbors, find the one which promises the
                # lowest distance to reach the destination satellite
                best_distance_m = 1000000000000000
                #dst_sat = int(dst_sat)
                for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                    distance_m = (
                        sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                        +
                        dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                    )
                    if distance_m < best_distance_m:
                        next_hop_decision = (
                            neighbor_id,
                            sat_neighbor_to_if[(curr, neighbor_id)],
                            sat_neighbor_to_if[(neighbor_id, curr)]
                        )
                    best_distance_m = distance_m

            else:
                # This is the destination satellite, as such the next hop is the ground station itself
                #print(num_isls_per_sat[dst_sat])
                #print(gid_to_sat_gsl_if_idx[dst_gs_node_id])
                next_hop_decision = (
                    dst_gs_node_id,
                    num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                    0
                )

            # In any case, save the distance of the satellite to the ground station to re-use
            # when we calculate ground station to ground station forwarding
            dist_satellite_to_ground_station[(curr, dst_gs_node_id)].append(distance_to_ground_station_m)

            # Write to forwarding state
            if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                f_out.write("%d,%d,%d,%d,%d\n" % (
                    curr,
                    dst_gs_node_id,
                    next_hop_decision[0],
                    next_hop_decision[1],
                    next_hop_decision[2]
                ))
            fstate[(curr, dst_gs_node_id)] = next_hop_decision
            #print("Print fstate curr")
        # Adding src_gs to the fstate
        # By default, if there is no satellite in range for one of the
        # ground stations, it will be dropped (indicated by -1)
        next_hop_decision = (
            src_sat,
            0,
            num_isls_per_sat[src_sat] + gid_to_sat_gsl_if_idx[src_gid]
        )

        # Update forwarding state
        if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
            f_out.write("%d,%d,%d,%d,%d\n" % (
                src_gs_node_id,
                dst_gs_node_id,
                next_hop_decision[0],
                next_hop_decision[1],
                next_hop_decision[2]
            ))
        fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision
        #print("Final fstate")
    return fstate
"""
def calculate_fstate_shortest_path_oscar(
        output_dynamic_state_dir,
        results_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_complete,
        sat_net_graph_only_satellites_with_isls,
        ground_station_satellites_in_range_candidates,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        sat_neighbor_to_if,
        prev_fstate,
        src_gs_node_id,
        dst_gs_node_id,
        enable_verbose_logs
):
    
    print("SRC_gs: ", src_gs_node_id)
    print("DST_gs: ", dst_gs_node_id)
    transmission_time_s = 1 * 10**-3
    for edge in sat_net_graph_complete.edges(data=True):
        #edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)
        edge[2]['weight'] += transmission_time_s * 299792458.0

    for edge in sat_net_graph_only_satellites_with_isls.edges(data=True):
        #edge[2]['weight'] = math.log10((edge[2]['weight']) / 1000)
        edge[2]['weight'] += transmission_time_s * 299792458.0


    # Perform shortest path calculation global graph 
    dist_sat_net_complete = nx.floyd_warshall_numpy(sat_net_graph_complete)
    # Perform shortest path calculation between satellites
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)
    
    output_filename_test = output_dynamic_state_dir + "Shortest_dists_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename_test, "w+") as f_out_2:
        for src_gid in range(num_ground_stations):
                for dst_gid in range(num_ground_stations):
                    if src_gid != dst_gid:
                        src_gs_node_id_temp = num_satellites + src_gid
                        dst_gs_node_id_temp = num_satellites + dst_gid
                        edge_weight = dist_sat_net_complete[(src_gs_node_id_temp, dst_gs_node_id_temp)]
                        f_out_2.write(f"src_gs_node_id: {src_gs_node_id_temp}, dst_gs_node_id: {dst_gs_node_id_temp}, edge_weight: {edge_weight}\n")

    # Now, find src_sat and dst_satthat promise the shortest path
    best_src_dst_sats_dic = {}
    if src_gs_node_id != dst_gs_node_id:
        #src_gs_node_id_temp = num_satellites + src_gid
        #dst_gs_node_id_temp = num_satellites + dst_gid
        src_gid = src_gs_node_id - num_satellites
        dst_gid = dst_gs_node_id - num_satellites
        #print(ground_station_satellites_in_range_candidates)
        #print(dst_gid)
        possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
        #print(possible_src_sats)
        possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
        #print(possible_dst_sats)
        src_sat = 0
        dst_sat = 0
        total_dist = 1000000000000000
        for a in possible_src_sats:
            #a = satellite_info[1]
            dist_sat_src_gs = sat_net_graph_complete.edges[(a[1], src_gs_node_id)]["weight"]
            for b in possible_dst_sats:
                if a != b:
                    dist_sat_dst_gs = sat_net_graph_complete.edges[(b[1], dst_gs_node_id)]["weight"]
                    dist_isl = dist_sat_net_without_gs[(a[1], b[1])]
                    dist_total = dist_sat_src_gs + dist_sat_dst_gs + dist_isl
                    #print("SRC: ", src_gs_node_id)
                    #print("SRC: ", dst_gs_node_id)
                    #print("Total Dist: ", dist_total)
                    #print("Dist SAt Net Complete: ", dist_sat_net_complete[(src_gs_node_id, dst_gs_node_id)])
                    if dist_total <= total_dist:
                        #print("Enter IF")
                        src_sat = a[1]
                        dst_sat = b[1]
                        total_dist = dist_total
                        gs_src_sat_dist = dist_sat_src_gs
                        dst_sat_gs_dist = dist_sat_dst_gs
                        isl_dist = dist_isl
                        shortest_path = nx.shortest_path(sat_net_graph_only_satellites_with_isls, source=src_sat, target=dst_sat, weight='weight')

                        # Calculate the weight of each edge in the shortest path
                        edge_weights = [(shortest_path[i], shortest_path[i + 1], sat_net_graph_only_satellites_with_isls[shortest_path[i]][shortest_path[i + 1]]['weight'])
                            for i in range(len(shortest_path) - 1)]

                        #print("Shortest path from node {} to node {}: {}".format(src_sat, dst_sat, shortest_path))
                        #print("Edge weights along the path: {}".format(edge_weights))

                        #output_str = f"Time: {time_since_epoch_ns}, Src_sat: {src_sat}, Dst_sat: {dst_sat}, Src_gs: {src_gs_node_id}, Dst_gs: {dst_gs_node_id}\nPower_to_src_sat: {gs_src_sat_dist}, Dist_to_src_sat: {(10**(gs_src_sat_dist))*1000}\nDist_ISL: {isl_dist}, Power_to_dst_sat: {dst_sat_gs_dist}, Dist_to_dst_sat: {(10**(dst_sat_gs_dist) * 1000)} \nTotal_dist: {total_dist} \n"
                        output_str = f"Time: {time_since_epoch_ns}, Src_sat: {src_sat}, Dst_sat: {dst_sat}, Src_gs: {src_gs_node_id}, Dst_gs: {dst_gs_node_id}\nPower_to_src_sat: {(gs_src_sat_dist)**2}, Dist_to_src_sat: {(gs_src_sat_dist)}\nDist_ISL: {isl_dist}, Power_to_dst_sat: {(dst_sat_gs_dist)**2}, Dist_to_dst_sat: {dst_sat_gs_dist} \nTotal_dist: {total_dist} \n"
                        counter = 1
                        for edge_weight in edge_weights:
                            if counter < len(edge_weights):
                                #output_str += f"Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {edge_weight[2]} WeightDistance: {(10**(edge_weight[2])) * 1000}, "
                                output_str += f" Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {(edge_weight[2])**2} WeightDistance: {(edge_weight[2])}, "
                                counter += 1
                            else:
                                #output_str += f"Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {edge_weight[2]} WeightDistance: {(10**(edge_weight[2])) * 1000}"
                                output_str += f" Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {(edge_weight[2])**2} WeightDistance: {(edge_weight[2])}"
                        # Append total distance or any other relevant information
                        output_str += f"\nTotal_dist: {total_dist}\n"
                        best_src_dst_sats_dic = {
                            'src_gs_node_id': src_gs_node_id,
                            'dst_gs_node_id': dst_gs_node_id,
                            'src_sat': src_sat,
                            'dst_sat': dst_sat
                        }
                else:
                    dist_sat_dst_gs = sat_net_graph_complete.edges[(a[1], dst_gs_node_id)]["weight"]
                    dist_isl = 0 #dist_sat_net_without_gs[(a[1], b[1])]
                    dist_total = dist_sat_src_gs + dist_sat_dst_gs + dist_isl
                    #print("SRC: ", src_gs_node_id)
                    #print("SRC: ", dst_gs_node_id)
                    #print("Total Dist: ", dist_total)
                    #print("Dist SAt Net Complete: ", dist_sat_net_complete[(src_gs_node_id, dst_gs_node_id)])
                    if dist_total <= total_dist:
                        #print("Enter IF")
                        src_sat = a[1]
                        dst_sat = a[1]
                        total_dist = dist_total
                        gs_src_sat_dist = dist_sat_src_gs
                        dst_sat_gs_dist = dist_sat_dst_gs
                        isl_dist = dist_isl
                        shortest_path = nx.shortest_path(sat_net_graph_only_satellites_with_isls, source=src_sat, target=dst_sat, weight='weight')

                        # Calculate the weight of each edge in the shortest path
                        edge_weights = [(shortest_path[i], shortest_path[i + 1], sat_net_graph_only_satellites_with_isls[shortest_path[i]][shortest_path[i + 1]]['weight'])
                            for i in range(len(shortest_path) - 1)]

                        #print("Shortest path from node {} to node {}: {}".format(src_sat, dst_sat, shortest_path))
                        #print("Edge weights along the path: {}".format(edge_weights))

                        #output_str = f"Time: {time_since_epoch_ns}, Src_sat: {src_sat}, Dst_sat: {dst_sat}, Src_gs: {src_gs_node_id}, Dst_gs: {dst_gs_node_id}\nPower_to_src_sat: {gs_src_sat_dist}, Dist_to_src_sat: {(10**(gs_src_sat_dist))*1000}\nDist_ISL: {isl_dist}, Power_to_dst_sat: {dst_sat_gs_dist}, Dist_to_dst_sat: {(10**(dst_sat_gs_dist) * 1000)} \nTotal_dist: {total_dist} \n"
                        output_str = f"Time: {time_since_epoch_ns}, Src_sat: {src_sat}, Dst_sat: {dst_sat}, Src_gs: {src_gs_node_id}, Dst_gs: {dst_gs_node_id}\nPower_to_src_sat: {(gs_src_sat_dist)**2}, Dist_to_src_sat: {(gs_src_sat_dist)}\nDist_ISL: {isl_dist}, Power_to_dst_sat: {(dst_sat_gs_dist)**2}, Dist_to_dst_sat: {dst_sat_gs_dist} \nTotal_dist: {total_dist} \n"
                        counter = 1
                        for edge_weight in edge_weights:
                            if counter < len(edge_weights):
                                #output_str += f"Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {edge_weight[2]} WeightDistance: {(10**(edge_weight[2])) * 1000}, "
                                output_str += f" Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {(edge_weight[2])**2} WeightDistance: {(edge_weight[2])}, "
                                counter += 1
                            else:
                                #output_str += f"Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {edge_weight[2]} WeightDistance: {(10**(edge_weight[2])) * 1000}"
                                output_str += f" Edge: {edge_weight[0]}-{edge_weight[1]} WeightPower: {(edge_weight[2])**2} WeightDistance: {(edge_weight[2])}"
                        # Append total distance or any other relevant information
                        output_str += f"\nTotal_dist: {total_dist}\n"
                        best_src_dst_sats_dic = {
                            'src_gs_node_id': src_gs_node_id,
                            'dst_gs_node_id': dst_gs_node_id,
                            'src_sat': src_sat,
                            'dst_sat': dst_sat
                        }
    
    #print(src_sat)
    #print(dst_sat)
    output_filename_path = results_dir + "/Time_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename_path, "w+") as f_out_3:
        f_out_3.write(output_str)
    #print(src_sat)
    #print(dst_sat)
    #print(dist_total)
    # Forwarding state
    
    fstate = {}
    output_filename = output_dynamic_state_dir + "/fstate_" + str(src_gs_node_id) + "_to_" + str(dst_gs_node_id) + "_" + str(time_since_epoch_ns) + ".txt"
    with open(output_filename, "w+") as f_out:
    #return best_src_dst_sats
        #src_sat = best_src_dst_sats_dic['src_sat']
        #dst_sat = best_src_dst_sats_dic['dst_sat']
        #src_sat, dst_sat = best_src_dst_sats_dic.get((src_gs_node_id, dst_gs_node_id), None)
        #f_out_2.write(f"src_gs_node_id: {src_gs_node_id}, dst_gs_node_id: {dst_gs_node_id}, src_sat: {src_sat}, dst_sat: {dst_sat}\n")
        dist_satellite_to_ground_station = {}
        #print(prev_fstate)
        for curr in range(num_satellites):
            next_hop_decision = (-1, -1, -1)
            distance_to_ground_station_m = float("inf")
            dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = []
            # If the current node is not that satellite, determine how to get to the satellite
            if curr != dst_sat:

                # Among its neighbors, find the one which promises the
                # lowest distance to reach the destination satellite
                best_distance_m = 1000000000000000
                #dst_sat = int(dst_sat)
                for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                    distance_m = (
                        sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                        +
                        dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                    )
                    if distance_m < best_distance_m:
                        next_hop_decision = (
                            neighbor_id,
                            sat_neighbor_to_if[(curr, neighbor_id)],
                            sat_neighbor_to_if[(neighbor_id, curr)]
                        )
                    best_distance_m = distance_m

            else:
                # This is the destination satellite, as such the next hop is the ground station itself
                #print(num_isls_per_sat[dst_sat])
                #print(gid_to_sat_gsl_if_idx[dst_gs_node_id])
                next_hop_decision = (
                    dst_gs_node_id,
                    num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                    0
                )

            # In any case, save the distance of the satellite to the ground station to re-use
            # when we calculate ground station to ground station forwarding
            dist_satellite_to_ground_station[(curr, dst_gs_node_id)].append(distance_to_ground_station_m)

            # Write to forwarding state
            if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                f_out.write("%d,%d,%d,%d,%d\n" % (
                    curr,
                    dst_gs_node_id,
                    next_hop_decision[0],
                    next_hop_decision[1],
                    next_hop_decision[2]
                ))
            fstate[(curr, dst_gs_node_id)] = next_hop_decision
            #print("Print fstate curr")
        # Adding src_gs to the fstate
        # By default, if there is no satellite in range for one of the
        # ground stations, it will be dropped (indicated by -1)
        next_hop_decision = (
            src_sat,
            0,
            num_isls_per_sat[src_sat] + gid_to_sat_gsl_if_idx[src_gid]
        )

        # Update forwarding state
        if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
            f_out.write("%d,%d,%d,%d,%d\n" % (
                src_gs_node_id,
                dst_gs_node_id,
                next_hop_decision[0],
                next_hop_decision[1],
                next_hop_decision[2]
            ))
        fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision
        #print("Final fstate")
    return fstate