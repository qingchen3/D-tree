# 13 millions insertions and 2K deletions on stackoverflow

import sys
import random
from _collections import defaultdict
from HK import HK_utils
from utils import tree_utils
from utils.tree_utils import constructST_adjacency_list
from utils.graph_utils import loadGraph
from Dtree import Dtree_utils
from Dtree.DTNode import DTNode
from HK.HKNode import HKNode
from timeit import default_timer as timer
import HK.updates as HKupdate
from Class.Res import Res
from utils.IO import setup, printRes, output_average_dist_by_method, update_maintanence, update_res_query_Sd, \
    update_res_vertices_edges, update_average_distance, update_average_uneven_size_beta, update_average_runtime,\
    copyRes
from utils.graph_utils import order
from utils.tree_utils import generatePairs


if __name__ == '__main__':
    sys.setrecursionlimit(50000000)
    folder = 'dataset/'
    testcase = sys.argv[1]
    records = loadGraph(testcase)

    #if testcase != 'stackoverflow':
    #    raise ValueError("filename has to be stackoverflow.")

    isSmallGraph = False  # True: not test opt; False: test opt
    sanity_check = False

    # setup starting point and ending point
    start_timestamp = records[0][2]
    end_timestamp = records[-1][2]

    #  setups
    survival_time, test_points = setup(testcase, start_timestamp, end_timestamp)
    # sanity_check = True  # True: switch on the sanity check; False: swith off the sanity check.

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

    edges = set()
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

            edges.add((a, b))

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

        current_time += 1
        tt = 40
        if current_time in test_points:
            for (a, b) in random.sample(list(edges), tt):
                edges.remove((a, b))
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
                    assert Dtree[a].size == nDtree[a].size
                if Dtree[b].parent is None and Dtree[b].size == 1:
                    v_set.remove(b)
                    assert Dtree[b].size == nDtree[b].size

            #del expiredDict[current_time]

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

            # evaluate query performance
            # v_list = list(v_set)
            print("generate pairs")
            test_edges = generatePairs(v_set)
            print("complete generating pairs")

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

            if isSmallGraph:
                query_output_text = "all pairs"
            else:
                query_output_text = "samples"

            # output to terminal
            query_data = []
            query_data.append(["nDtree", query_output_text, query_nDtree])
            query_data.append(["Dtree", query_output_text, query_Dtree])
            query_data.append(["HK", query_output_text, query_HK])
            printRes("connectivity query", query_data)


    print("# of total updates: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count +
                                 Dtree_res.de_nte_count + Dtree_res.de_te_count))
    print("# of insertions: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count))
    print("# of deletions: %d." %(Dtree_res.de_nte_count + Dtree_res.de_te_count))





