import sys
import random
from _collections import defaultdict
from ET import ET_utils
from HK import HK_utils
from utils import tree_utils
from utils.tree_utils import constructST_adjacency_list
from utils.graph_utils import loadGraph

from Dtree import Dtree_utils
from ET.ETNode import ETNode
from Dtree.DTNode import DTNode
from HK.HKNode import HKNode
from timeit import default_timer as timer

import HK.updates as HKupdate
import ET.updates as ETupdate

from Class.Res import Res
from utils.IO import setup, printRes, output_average_dist_by_method, update_maintanence, update_res_query_Sd, \
    update_res_vertices_edges, update_average_distance, update_average_uneven_size_beta, update_average_runtime,\
    copyRes
from utils.graph_utils import best_BFS, order
from utils.tree_utils import generatePairs


if __name__ == '__main__':
    sys.setrecursionlimit(50000000)
    folder = 'dataset/'
    testcase = sys.argv[1]
    records = loadGraph(testcase)

    # setup starting point and ending point
    start_timestamp = records[0][2]
    end_timestamp = records[-1][2]

    # As described in the paper, we slightly change the start_timestamp
    # (and end_timestamp), which includes almost all edges
    if testcase == 'dblp':
        start_timestamp = 1980
    elif testcase == 'dnc':
        start_timestamp = 1423298633
    elif testcase == 'enron':
        start_timestamp = 915445260
        end_timestamp = 1040459085

    #  setups
    survival_time, test_points = setup(testcase, start_timestamp, end_timestamp)
    sanity_check = True  # True: switch on the sanity check; False: swith off the sanity check.

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:  # small graphs
        isSmallGraph = True
        n = 200000  # n is setup for opt
    else:  # large graphs
        isSmallGraph = False  # True: not test opt; False: test opt
        n = 200000

    print(survival_time, "%d tests, first test: %d, last test: %d" %(len(test_points), test_points[0], test_points[-1]))
    print(start_timestamp, end_timestamp)
    print(test_points)

    # start from an empty graph
    idx = 0
    max_priority = sys.maxsize
    graph = defaultdict(set)
    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)

    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    _, nDtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    _, opt = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)

    ET_forest, ET_tree_edges, ET_non_tree_edges, ET_active_occurrence_dict, ET_tree_edges_pointers = \
        ET_utils.ET_constructSF(graph, 0, max_priority)
    HK_forest, HK_tree_edges, HK_non_tree_edges, HK_active_occurrence_dict, HK_tree_edges_pointers = \
        HK_utils.HK_constructSF(graph, 0, max_priority)

    expiredDict = defaultdict(set)
    inserted_edge = defaultdict()

    ET_res = Res()
    HK_res = Res()
    nDtree_res = Res()
    Dtree_res = Res()
    opt_res = Res()

    # results in previous test point
    ET_res_pre = Res()
    HK_res_pre = Res()
    nDtree_res_pre = Res()
    Dtree_res_pre = Res()
    opt_res_pre = Res()

    # distribution of distance between root and nodes
    Dtree_accumulated_dist = defaultdict(int)
    nDtree_accumulated_dist = defaultdict(int)
    HK_accumulated_dist = defaultdict(int)
    ET_accumulated_dist = defaultdict(int)
    opt_accumulated_dist = defaultdict(int)

    v_set = set()
    edges_num = 0
    current_time = start_timestamp
    count_snapshot = 0

    Dtree_sum_small_size = 0
    Dtree_sum_beta = 0

    nDtree_sum_small_size = 0
    nDtree_sum_beta = 0

    HK_sum_small_size = 0
    HK_sum_beta = 0

    # while current_time <= end_timestamp + survival_time:
    while current_time <= test_points[-1]:
        # loop records and start with the record with current_time

        while idx < len(records) and records[idx][2] < current_time:
            idx += 1
        while idx < len(records) and records[idx][2] == current_time:
            # filter out (v, v) edges
            if records[idx][0] == records[idx][1]:
                idx += 1
                continue

            a, b = order(records[idx][0], records[idx][1])
            v_set.add(a)
            v_set.add(b)

            idx += 1
            if (a, b) not in inserted_edge:  # a new edge
                inserted_edge[(a, b)] = current_time + survival_time  # we keep the expired time for the inserted edge.
                expiredDict[current_time + survival_time].add((a, b))
            else:  # re-insert this edge, refresh the expired timestamp
                expired_ts = inserted_edge[(a, b)]
                expiredDict[expired_ts].remove((a, b))
                inserted_edge[
                    (a, b)] = current_time + survival_time  # we refresh the expired time for the inserted edge.
                expiredDict[current_time + survival_time].add((a, b))

            # evaluate HK
            # initialize HKNode for HK if not exists
            if a not in HK_active_occurrence_dict:
                node = HKNode(a, random.randint(1, max_priority))
                node.active = True
                node.size = 1
                HK_active_occurrence_dict[a] = node

            if b not in HK_active_occurrence_dict:
                node = HKNode(b, random.randint(1, max_priority))
                node.active = True
                node.size = 1
                HK_active_occurrence_dict[b] = node

            start = timer()
            root_a, distance_a = tree_utils.find_root_with_steps(HK_active_occurrence_dict[a])
            root_b, distance_b = tree_utils.find_root_with_steps(HK_active_occurrence_dict[b])
            go_to_root_HK = timer() - start

            if root_a.val != root_b.val:
                HK_res.in_te_count += 1
                start = timer()
                HKupdate.insert_tree_edge(a, root_a, b, root_b, HK_tree_edges, HK_active_occurrence_dict,
                                                HK_tree_edges_pointers, max_priority)
                HK_res.in_te_time += (timer() - start + go_to_root_HK)

            else:  # a and b are connected
                # if (a, b) not in HK_tree_edges and (a, b) not in HK_non_tree_edges:  # (a, b) is a new  non-tree edge
                if (a, b) not in HK_tree_edges:
                    HK_res.in_nte_count += 1

                    # count running time for inserting a non tree edge in HK
                    start = timer()
                    HKupdate.insert_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                    HK_res.in_nte_time += (timer() - start + go_to_root_HK)

            # nDtree, navie Dtree
            if a not in nDtree:
                nDtree[a] = DTNode(a)
            if b not in nDtree:
                nDtree[b] = DTNode(b)

            start = timer()
            root_a, distance_a = Dtree_utils.find_root(nDtree[a])
            root_b, distance_b = Dtree_utils.find_root(nDtree[b])
            go_to_root_nDtree = timer() - start

            if root_a.val != root_b.val:
                nDtree_res.in_te_count += 1
                start = timer()
                Dtree_utils.insert_te_simple(nDtree[a], nDtree[b], root_a, root_b)
                nDtree_res.in_te_time += (timer() - start + go_to_root_nDtree)
            else:  # a and b are connected
                # (a, b) is a new  non tree edge
                # if not (nDtree[a].parent == nDtree[b] or nDtree[b].parent == nDtree[a]) and \
                #        not (nDtree[a] in nDtree[b].nte and nDtree[b] in nDtree[a].nte):
                if not (nDtree[a].parent == nDtree[b] or nDtree[b].parent == nDtree[a]):
                    # inserting a non tree edge
                    nDtree_res.in_nte_count += 1

                    # count running time for inserting a non tree edge in DT
                    start = timer()
                    Dtree_utils.insert_nte_simple(nDtree[a], nDtree[b])
                    nDtree_res.in_nte_time += (timer() - start + go_to_root_nDtree)

            if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                raise ValueError("Error in insertion")

            # Dtree
            if a not in Dtree:
                Dtree[a] = DTNode(a)
            if b not in Dtree:
                Dtree[b] = DTNode(b)

            start = timer()
            root_a, distance_a = Dtree_utils.find_root(Dtree[a])
            root_b, distance_b = Dtree_utils.find_root(Dtree[b])
            go_to_root_Dtree = timer() - start

            if root_a.val != root_b.val:
                edges_num += 1
                Dtree_res.in_te_count += 1
                start = timer()
                Dtree_utils.insert_te(Dtree[a], Dtree[b], root_a, root_b)
                Dtree_res.in_te_time += (timer() - start + go_to_root_Dtree)
            else:  # a and b are connected
                # (a, b) is a new  non tree edge
                # if not (Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]) and \
                #        not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[a].nte):
                if not (Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]):
                    if not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[a].nte):
                        edges_num += 1
                    # inserting a non tree edge
                    Dtree_res.in_nte_count += 1

                    # count running time for inserting a non tree edge in DT
                    start = timer()
                    Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
                    Dtree_res.in_nte_time += (timer() - start + go_to_root_Dtree)

            if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                raise ValueError("Error in insertion")

            if isSmallGraph:  # evaluations on small graphs
                # ET
                # only evaluate ET-tree for small graphs, since it is very inefficient for large graphs
                # initialize ET Node if not exists
                if a not in ET_active_occurrence_dict:
                    node = ETNode(a, random.randint(1, max_priority))
                    node.active = True
                    ET_active_occurrence_dict[a] = node
                if b not in ET_active_occurrence_dict:
                    node = ETNode(b, random.randint(1, max_priority))
                    node.active = True
                    ET_active_occurrence_dict[b] = node

                start = timer()
                root_a, distance_a = tree_utils.find_root_with_steps(ET_active_occurrence_dict[a])
                root_b, distance_b = tree_utils.find_root_with_steps(ET_active_occurrence_dict[b])
                go_to_root_ET = timer() - start

                if root_a.val != root_b.val:
                    ET_res.in_te_count += 1
                    start = timer()
                    ETupdate.insert_tree_edge(a, root_a, b, root_b, ET_tree_edges,
                                                   ET_active_occurrence_dict,
                                                   ET_tree_edges_pointers, max_priority)
                    ET_res.in_te_time += (timer() - start + go_to_root_ET)

                else:  # a and b are connected
                    # if (a, b) not in ET_tree_edges and (
                    #        a, b) not in ET_non_tree_edges:  # (a, b) is a new  non tree edge
                    if not (a, b) in ET_tree_edges:
                        ET_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in ET
                        start = timer()
                        ETupdate.insert_nontree_edge(a, b, ET_active_occurrence_dict, ET_non_tree_edges)
                        ET_res.in_nte_time += (timer() - start + go_to_root_ET)

                if sanity_check and tree_utils.query(a, b, ET_active_occurrence_dict) != \
                        tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in insertion")

                # opt
                graph[a].add(b)
                graph[b].add(a)
                if a not in opt:
                    opt[a] = DTNode(a)
                if b not in opt:
                    opt[b] = DTNode(b)

                start = timer()
                root_a, distance_a = Dtree_utils.find_root(opt[a])
                root_b, distance_b = Dtree_utils.find_root(opt[b])
                go_to_root_opt = timer() - start

                if root_a.val != root_b.val:

                    opt_res.in_te_count += 1
                    start = timer()

                    Dtree_utils.insert_te_simple(opt[a], opt[b], root_a, root_b)

                    target = best_BFS(graph, n, a)  # find the root of best BFS-tree
                    Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set()) # reconstruct D-tree
                    opt_res.in_te_time += (timer() - start + go_to_root_opt)

                else:  # a and b are connected
                    # (a, b) is a new  non tree edge
                    if not (opt[a].parent == opt[b] or opt[b].parent == opt[a]) and \
                          not (opt[a] in opt[b].nte and opt[b] in opt[a].nte):
                        opt_res.in_nte_count += 1

                        start = timer()
                        target = best_BFS(graph, n, a)  # find the best BFS-tree
                        Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set())

                        # if target != root_a.val: # reconstruct the BFS tree
                        #   BFStree_utils.reconstruct_BFS_tree(opt[target], opt, set())
                        opt[a].nte.add(opt[b])
                        opt[b].nte.add(opt[a])
                        opt_res.in_nte_time += (timer() - start + go_to_root_opt)
                if sanity_check and Dtree_utils.query_simple(opt[a], opt[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in insertion")

        if current_time in expiredDict:

            for (a, b) in expiredDict[current_time]:
                del inserted_edge[(a, b)]
                edges_num -= 1
                # HK
                if (a, b) in HK_non_tree_edges:
                    HK_res.de_nte_count += 1
                    start = timer()
                    HKupdate.delete_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                    HK_res.de_nte_time += (timer() - start)
                else:
                    HK_res.de_te_count += 1
                    start = timer()
                    small_size, beta = HKupdate.delete_tree_edge(a, b, HK_tree_edges, HK_non_tree_edges,
                                        HK_active_occurrence_dict, HK_tree_edges_pointers, max_priority)
                    HK_res.de_te_time += (timer() - start)
                    HK_sum_small_size += small_size
                    HK_sum_beta += beta

                # nDtree, naive Dtree
                if nDtree[a] in nDtree[b].nte or nDtree[b] in nDtree[a].nte:
                    nDtree_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils.delete_nte(nDtree[a], nDtree[b])
                    nDtree_res.de_nte_time += (timer() - start)
                else:
                    nDtree_res.de_te_count += 1
                    start = timer()
                    _, _, small_size, beta = Dtree_utils.delete_te_simple(nDtree[a], nDtree[b])
                    nDtree_res.de_te_time += (timer() - start)

                    nDtree_sum_small_size += small_size
                    nDtree_sum_beta += beta

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in deletion")

                # Dtree
                if Dtree[a] in Dtree[b].nte or Dtree[b] in Dtree[a].nte:
                    Dtree_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils.delete_nte(Dtree[a], Dtree[b])
                    Dtree_res.de_nte_time += (timer() - start)
                else:
                    Dtree_res.de_te_count += 1
                    start = timer()
                    _, _, small_size, beta = Dtree_utils.delete_te(Dtree[a], Dtree[b])
                    Dtree_res.de_te_time += (timer() - start)

                    Dtree_sum_small_size += small_size
                    Dtree_sum_beta += beta

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in deletion in Dtree")

                # remove isolated nodes from v_set.
                if Dtree[a].parent is None and Dtree[a].size == 1:
                    v_set.remove(a)
                    if Dtree[a].size != nDtree[a].size:
                        print(Dtree[a].size, nDtree[a].size)
                    assert Dtree[a].size == nDtree[a].size
                if Dtree[b].parent is None and Dtree[b].size == 1:
                    v_set.remove(b)
                    if Dtree[b].size != nDtree[b].size:
                        print(Dtree[b].size, nDtree[b].size)
                    assert Dtree[b].size == nDtree[b].size

                # evaluate ET-tree and opt on small graphs
                if isSmallGraph:
                    # ET
                    if (a, b) in ET_non_tree_edges:
                        ET_res.de_nte_count += 1
                        start = timer()
                        ETupdate.delete_nontree_edge(a, b, ET_active_occurrence_dict, ET_non_tree_edges)
                        ET_res.de_nte_time += (timer() - start)
                    else:
                        ET_res.de_te_count += 1
                        start = timer()
                        ETupdate.delete_tree_edge(a, b, ET_tree_edges, ET_non_tree_edges,
                                            ET_active_occurrence_dict, ET_tree_edges_pointers,
                                            max_priority)
                        ET_res.de_te_time += (timer() - start)
                    if sanity_check and tree_utils.query(a, b, ET_active_occurrence_dict) != tree_utils.query(a, b, HK_active_occurrence_dict):
                        raise ValueError("Error in insertion in opt")

                    # opt
                    graph[a].remove(b)
                    graph[b].remove(a)

                    if opt[a] in opt[b].nte or opt[b] in opt[a].nte:
                        opt_res.de_nte_count += 1
                        start = timer()
                        Dtree_utils.delete_nte(opt[a], opt[b])

                        target = best_BFS(graph, n, a)  # find the root of the best BFS-tree
                        Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set())  # reconstruct the opt
                        opt_res.de_nte_time += (timer() - start)
                    else:
                        opt_res.de_te_count += 1
                        start = timer()
                        res = Dtree_utils.delete_te(opt[a], opt[b])
                        if type(res) is tuple: # delete tree edge (a, b) splits a spanning tree
                            target_a = best_BFS(graph, n, a)  # find root of the best BFS-tree contains a
                            target_b = best_BFS(graph, n, b)  # find root of the best BFS-tree contain b
                            Dtree_utils.reconstruct_BFS_tree(opt[target_a], opt, set())  # reconstruct the opt
                            Dtree_utils.reconstruct_BFS_tree(opt[target_b], opt, set())  # reconstruct the opt
                        else:
                            target = best_BFS(graph, n, a)  # find the root of the best BFS-tree
                            Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set())  # reconstruct the opt
                        opt_res.de_te_time += (timer() - start)

                    if sanity_check and Dtree_utils.query_simple(opt[a], opt[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                        raise ValueError("Error in insertion in opt")

            del expiredDict[current_time]
        current_time += 1
        if current_time in test_points:
            # output to terminal
            print("timestamp:%d" % current_time)
            insertion_nte_data = list()
            insertion_nte_data.append(["nDtree", nDtree_res.in_nte_count, nDtree_res.in_nte_time])
            insertion_nte_data.append(["Dtree", Dtree_res.in_nte_count, Dtree_res.in_nte_time])
            insertion_nte_data.append(["HK", HK_res.in_nte_count, HK_res.in_nte_time])
            if isSmallGraph:
                insertion_nte_data.append(["ET", ET_res.in_nte_count, ET_res.in_nte_time])
                insertion_nte_data.append(["opt", opt_res.in_nte_count, opt_res.in_nte_time])
            printRes("inserting non tree edge", insertion_nte_data)
            print()

            insertion_te_data = list()
            insertion_te_data.append(["nDtree", nDtree_res.in_te_count, nDtree_res.in_te_time])
            insertion_te_data.append(["Dtree", Dtree_res.in_te_count, Dtree_res.in_te_time])
            insertion_te_data.append(["HK", HK_res.in_te_count, HK_res.in_te_time])
            if isSmallGraph:
                insertion_te_data.append(["ET", ET_res.in_te_count, ET_res.in_te_time])
                insertion_te_data.append(["opt", opt_res.in_te_count, opt_res.in_te_time])
            printRes("inserting tree edge", insertion_te_data)
            print()

            deletion_nte_data = list()
            deletion_nte_data.append(["nDtree", nDtree_res.de_nte_count, nDtree_res.de_nte_time])
            deletion_nte_data.append(["Dtree", Dtree_res.de_nte_count, Dtree_res.de_nte_time])
            deletion_nte_data.append(["HK", HK_res.de_nte_count, HK_res.de_nte_time])
            if isSmallGraph:
                deletion_nte_data.append(["ET", ET_res.de_nte_count, ET_res.de_nte_time])
                deletion_nte_data.append(["opt", opt_res.de_nte_count, opt_res.de_nte_time])
            printRes("deleting non tree edge", deletion_nte_data)
            print()

            deletion_te_data = list()
            deletion_te_data.append(["nDtree", nDtree_res.de_te_count, nDtree_res.de_te_time])
            deletion_te_data.append(["Dtree", Dtree_res.de_te_count, Dtree_res.de_te_time])
            deletion_te_data.append(["HK", HK_res.de_te_count, HK_res.de_te_time])
            if isSmallGraph:
                deletion_te_data.append(["ET", ET_res.de_te_count, ET_res.de_te_time])
                deletion_te_data.append(["opt", opt_res.de_te_count, opt_res.de_te_time])
            printRes("deleting tree edge", deletion_te_data)
            print()

            # first get the distance to root. Then calculate Sd and accumulated Sd for all snapshots.
            ET_Sd = 0
            HK_Sd = 0
            opt_Sd = 0
            Dtree_Sd = 0
            nDtree_Sd = 0
            for v in v_set:
                Dtree_d = Dtree_utils.toRoot(Dtree[v])
                Dtree_Sd += Dtree_d
                Dtree_accumulated_dist[Dtree_d] += 1

                nDtree_d = Dtree_utils.toRoot(nDtree[v])
                nDtree_Sd += nDtree_d
                nDtree_accumulated_dist[nDtree_d] += 1

                HK_d = tree_utils.toRoot(HK_active_occurrence_dict[v])
                HK_Sd += HK_d
                HK_accumulated_dist[HK_d] += 1

                if isSmallGraph:
                    ET_d = tree_utils.toRoot(ET_active_occurrence_dict[v])
                    ET_Sd += ET_d
                    ET_accumulated_dist[ET_d] += 1

                    opt_d = Dtree_utils.toRoot(opt[v])
                    opt_Sd += opt_d
                    opt_accumulated_dist[opt_d] += 1

            # evaluate query performance
            # v_list = list(v_set)
            test_edges = generatePairs(v_set)

            start = timer()
            for (x, y) in test_edges:
                Dtree_utils.query_simple(nDtree[x], nDtree[y])
            query_nDtree = timer() - start

            start = timer()
            for (x, y) in test_edges:
                Dtree_utils.query(Dtree[x], Dtree[y])
            query_Dtree = timer() - start

            start = timer()
            for (x, y) in test_edges:
                tree_utils.query(x, y, HK_active_occurrence_dict)
            query_HK = timer() - start

            query_ET = 0
            query_opt = 0
            if isSmallGraph:
                start = timer()
                for (x, y) in test_edges:
                    tree_utils.query(x, y, ET_active_occurrence_dict)
                query_ET = timer() - start

                start = timer()
                for (x, y) in test_edges:
                    Dtree_utils.query_simple(opt[x], opt[y])
                query_opt = timer() - start

            if isSmallGraph:
                query_output_text = "all pairs"
            else:
                query_output_text = "samples"

            # output to terminal
            query_data = []
            query_data.append(["nDtree", query_output_text, query_nDtree])
            query_data.append(["Dtree", query_output_text, query_Dtree])
            query_data.append(["HK", query_output_text, query_HK])

            Sd_data = list()
            Sd_data.append(["nDtree", "", nDtree_Sd])
            Sd_data.append(["Dtree", "", Dtree_Sd])
            Sd_data.append(["HK", "", HK_Sd])

            if isSmallGraph:
                query_data.append(["ET", query_output_text, query_ET])
                query_data.append(["opt", query_output_text, query_opt])

                Sd_data.append(["ET", "", ET_Sd])
                Sd_data.append(["opt", "", opt_Sd])

            printRes("connectivity query", query_data)
            printRes("S_d", Sd_data)

            """ All below are outputing results """
            # output results to file
            count_snapshot += 1
            output_average_dist_by_method(Dtree_accumulated_dist, count_snapshot, testcase, 'Dtree')
            output_average_dist_by_method(nDtree_accumulated_dist, count_snapshot, testcase, 'nDtree')
            output_average_dist_by_method(HK_accumulated_dist, count_snapshot, testcase, 'HK')

            update_res_query_Sd(testcase, 'query', [current_time, query_Dtree], 'Dtree')
            update_res_query_Sd(testcase, 'query', [current_time, query_nDtree], 'nDtree')
            update_res_query_Sd(testcase, 'query', [current_time, query_HK], 'HK')

            update_res_query_Sd(testcase, 'Sd', [current_time, Dtree_Sd], 'Dtree')
            update_res_query_Sd(testcase, 'Sd', [current_time, nDtree_Sd], 'nDtree')
            update_res_query_Sd(testcase, 'Sd', [current_time, HK_Sd], 'HK')

            update_maintanence(testcase, Dtree_res, 'Dtree')
            update_maintanence(testcase, nDtree_res, 'nDtree')
            update_maintanence(testcase, HK_res, 'HK')

            update_res_vertices_edges(testcase, 'vertices', [current_time, len(v_set)])
            update_res_vertices_edges(testcase, 'edges', [current_time, edges_num])

            update_average_distance(testcase, [current_time, Dtree_Sd / (len(v_set) + 0.000001)], 'Dtree')
            update_average_distance(testcase, [current_time, nDtree_Sd / (len(v_set) + 0.000001)], 'nDtree')
            update_average_distance(testcase, [current_time, HK_Sd / (len(v_set) + 0.000001)], 'HK')
            print("Average distance:",
                  Dtree_Sd / (len(v_set) + 0.000001),
                  nDtree_Sd / (len(v_set) + 0.000001),
                HK_Sd / (len(v_set) + 0.000001))

            update_average_uneven_size_beta(testcase, 'uneven', [current_time,
                                            Dtree_sum_small_size/(Dtree_res.de_te_count + 0.000001)], 'Dtree')
            update_average_uneven_size_beta(testcase, 'uneven', [current_time,
                                            nDtree_sum_small_size/(nDtree_res.de_te_count + 0.000001)], 'nDtree')
            update_average_uneven_size_beta(testcase, 'uneven', [current_time,
                                            HK_sum_small_size/(HK_res.de_te_count + 0.000001)], 'HK')

            update_average_uneven_size_beta(testcase, 'beta', [current_time,
                                            Dtree_sum_beta/(Dtree_res.de_te_count + 0.000001)], 'Dtree')
            update_average_uneven_size_beta(testcase, 'beta', [current_time,
                                            nDtree_sum_beta/(nDtree_res.de_te_count + 0.000001)], 'nDtree')
            update_average_uneven_size_beta(testcase, 'beta', [current_time,
                                            HK_sum_beta/(HK_res.de_te_count + 0.000001)], 'HK')

            # results for updates
            # inserting tree edges
            update_average_runtime(testcase,
                                   "insertion_te",
                                   [current_time, (Dtree_res.in_te_time - Dtree_res_pre.in_te_time) /
                                    (Dtree_res.in_te_count - Dtree_res_pre.in_te_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "insertion_te",
                                   [current_time, (nDtree_res.in_te_time - nDtree_res_pre.in_te_time) /
                                    (nDtree_res.in_te_count - nDtree_res_pre.in_te_count + 0.00001)], 'nDtree')
            update_average_runtime(testcase,
                                   "insertion_te",
                                   [current_time, (HK_res.in_te_time - HK_res_pre.in_te_time) /
                                    (HK_res.in_te_count - HK_res_pre.in_te_count + 0.00001)], 'HK')

            # inserting non-tree edges
            update_average_runtime(testcase,
                                   "insertion_nte",
                                   [current_time, (Dtree_res.in_nte_time - Dtree_res_pre.in_nte_time) /
                                    (Dtree_res.in_nte_count - Dtree_res_pre.in_nte_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "insertion_nte",
                                   [current_time, (nDtree_res.in_nte_time - nDtree_res_pre.in_nte_time) /
                                    (nDtree_res.in_nte_count - nDtree_res_pre.in_nte_count + 0.00001)], 'nDtree')
            update_average_runtime(testcase,
                                   "insertion_nte",
                                   [current_time, (HK_res.in_nte_time - HK_res_pre.in_nte_time) /
                                    (HK_res.in_nte_count - HK_res_pre.in_nte_count + 0.00001)], 'HK')

            # deleting tree edges
            update_average_runtime(testcase,
                                   "deletion_te",
                                   [current_time, (Dtree_res.de_te_time - Dtree_res_pre.de_te_time) /
                                    (Dtree_res.de_te_count - Dtree_res_pre.de_te_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "deletion_te",
                                   [current_time, (nDtree_res.de_te_time - nDtree_res_pre.de_te_time) /
                                    (nDtree_res.de_te_count - nDtree_res_pre.de_te_count + 0.00001)], 'nDtree')
            update_average_runtime(testcase,
                                   "deletion_te",
                                   [current_time, (HK_res.de_te_time - HK_res_pre.de_te_time) /
                                    (HK_res.de_te_count - HK_res_pre.de_te_count + 0.00001)], 'HK')

            # deleting non-tree edges
            update_average_runtime(testcase,
                                   "deletion_nte",
                                   [current_time, (Dtree_res.de_nte_time - Dtree_res_pre.de_nte_time) /
                                    (Dtree_res.de_nte_count - Dtree_res_pre.de_nte_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "deletion_nte",
                                   [current_time, (nDtree_res.de_nte_time - nDtree_res_pre.de_nte_time) /
                                    (nDtree_res.de_nte_count - nDtree_res_pre.de_nte_count + 0.00001)], 'nDtree')
            update_average_runtime(testcase,
                                   "deletion_nte",
                                   [current_time, (HK_res.de_nte_time - HK_res_pre.de_nte_time) /
                                    (HK_res.de_nte_count - HK_res_pre.de_nte_count + 0.00001)], 'HK')

            copyRes(Dtree_res, Dtree_res_pre)
            copyRes(nDtree_res, nDtree_res_pre)
            copyRes(HK_res, HK_res_pre)

            if isSmallGraph:
                output_average_dist_by_method(ET_accumulated_dist, count_snapshot, testcase, 'ET')
                output_average_dist_by_method(opt_accumulated_dist, count_snapshot, testcase, 'opt')

                update_res_query_Sd(testcase, 'query', [current_time, query_ET], 'ET')
                update_res_query_Sd(testcase, 'query', [current_time, query_opt], 'opt')

                update_res_query_Sd(testcase, 'Sd', [current_time, ET_Sd], 'ET')
                update_res_query_Sd(testcase, 'Sd', [current_time, opt_Sd], 'opt')

                update_maintanence(testcase, ET_res, 'ET')
                update_maintanence(testcase, opt_res, 'opt')

                update_average_distance(testcase, [current_time, ET_Sd / (len(v_set) + 0.000001)], 'ET')
                update_average_distance(testcase, [current_time, opt_Sd / (len(v_set) + 0.000001)], 'opt')

                # inserting tree edges
                update_average_runtime(testcase,
                                       "insertion_te",
                                       [current_time, (ET_res.in_te_time - ET_res_pre.in_te_time) /
                                        (ET_res.in_te_count - ET_res_pre.in_te_count + 0.00001)], 'ET')
                update_average_runtime(testcase,
                                       "insertion_te",
                                       [current_time, (opt_res.in_te_time - opt_res_pre.in_te_time) /
                                        (opt_res.in_te_count - opt_res_pre.in_te_count + 0.00001)], 'opt')

                # inserting non-tree edges
                update_average_runtime(testcase,
                                       "insertion_nte",
                                       [current_time, (ET_res.in_nte_time - ET_res_pre.in_nte_time) /
                                        (ET_res.in_nte_count - ET_res_pre.in_nte_count + 0.00001)], 'ET')
                update_average_runtime(testcase,
                                       "insertion_nte",
                                       [current_time, (opt_res.in_nte_time - opt_res_pre.in_nte_time) /
                                        (opt_res.in_nte_count - opt_res_pre.in_nte_count + 0.00001)], 'opt')

                # deleting tree edges
                update_average_runtime(testcase,
                                       "deletion_te",
                                       [current_time, (ET_res.de_te_time - ET_res_pre.de_te_time) /
                                        (ET_res.de_te_count - ET_res_pre.de_te_count + 0.00001)], 'ET')
                update_average_runtime(testcase,
                                       "deletion_te",
                                       [current_time, (opt_res.de_te_time - opt_res_pre.de_te_time) /
                                        (opt_res.de_te_count - opt_res_pre.de_te_count + 0.00001)], 'opt')

                # deleting non-tree edges
                update_average_runtime(testcase,
                                       "deletion_nte",
                                       [current_time, (ET_res.de_nte_time - ET_res_pre.de_nte_time) /
                                        (ET_res.de_nte_count - ET_res_pre.de_nte_count + 0.00001)], 'ET')
                update_average_runtime(testcase,
                                       "deletion_nte",
                                       [current_time, (opt_res.de_nte_time - opt_res_pre.de_nte_time) /
                                        (opt_res.de_nte_count - opt_res_pre.de_nte_count + 0.00001)], 'opt')

                copyRes(ET_res, ET_res_pre)
                copyRes(opt_res, opt_res_pre)

    print("# of total updates: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count +
                                 Dtree_res.de_nte_count + Dtree_res.de_te_count))
    print("# of insertions: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count))
    print("# of deletions: %d." %(Dtree_res.de_nte_count + Dtree_res.de_te_count))





