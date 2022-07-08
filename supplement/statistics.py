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
from utils.IO import setup, printRes, output_average_dist, updateRes
from utils.graph_utils import best_BFS, order
import os
from matplotlib import pyplot as plt
import numpy as np


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
    survival_time, test_points, query_writer, Sd_writer = setup(testcase, start_timestamp, end_timestamp)
    query_writer = None
    Sd_writer = None
    sanity_check = False  # True: switch on the sanity check; False: swith off the sanity check.

    if testcase in ['fb', 'wiki', 'dnc', 'messages', 'call']:  # small graphs
        isSmallGraph = True
        n = 200000  # n is setup for opt
    else:  # large graphs
        isSmallGraph = False  # True: not test opt; False: test opt
        n = 200000

    if testcase in ['osmswitzerland', 'TX']:
        test_points = [1]
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

    # distribution of distance between root and nodes
    Dtree_dist_data = defaultdict(int)
    nDtree_dist_data = defaultdict(int)
    opt_dist_data = defaultdict(int)
    ET_dist_data = defaultdict(int)
    HK_dist_data = defaultdict(int)

    insertion_count = 0
    deletion_count = 0

    steps_DT_nte = 0
    steps_ET_nte = 0

    v_set = set()

    current_time = start_timestamp
    while current_time <= end_timestamp + survival_time:
        # loop records and start with the record with current_time

        while idx < len(records) and records[idx][2] < current_time:
            idx += 1
        inserted_edges = set()
        while idx < len(records) and records[idx][2] == current_time:
            # filter out (v, v) edges
            if records[idx][0] == records[idx][1]:
                idx += 1
                continue

            u, v = order(records[idx][0], records[idx][1])
            v_set.add(u)
            v_set.add(v)
            inserted_edges.add((u, v))

            idx += 1
            if (u, v) not in inserted_edge:  # a new edge
                inserted_edge[(u, v)] = current_time + survival_time  # we keep the expired time for the inserted edge.
                expiredDict[current_time + survival_time].add((u, v))
            else:  # re-insert this edge, refresh the expired timestamp
                expired_ts = inserted_edge[(u, v)]
                expiredDict[expired_ts].remove((u, v))
                inserted_edge[
                    (u, v)] = current_time + survival_time  # we refresh the expired time for the inserted edge.
                expiredDict[current_time + survival_time].add((u, v))

        insertion_count += len(inserted_edges)
        if len(inserted_edges) > 0:
            output_set = set()
            cc = 0
            for (a, b) in inserted_edges:
                cc += 1
                output_set.add(a)
                output_set.add(b)
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
                    if (a, b) not in HK_tree_edges and (a, b) not in HK_non_tree_edges:  # (a, b) is a new  non-tree edge

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
                    if not (nDtree[a].parent == nDtree[b] or nDtree[b].parent == nDtree[a]) and \
                            not (nDtree[a] in nDtree[b].nte and nDtree[b] in nDtree[a].nte):
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
                    Dtree_res.in_te_count += 1
                    start = timer()
                    Dtree_utils.insert_te(Dtree[a], Dtree[b], root_a, root_b)
                    Dtree_res.in_te_time += (timer() - start + go_to_root_Dtree)
                else:  # a and b are connected
                    # (a, b) is a new  non tree edge
                    if not (Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]) and \
                            not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[a].nte):
                        # inserting a non tree edge
                        Dtree_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in DT
                        start = timer()
                        Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
                        Dtree_res.in_nte_time += (timer() - start + go_to_root_Dtree)

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in insertion")
                if testcase == 'osmswitzerland':
                    div = 1000000
                else:
                    div = 100000
                if cc % div == 0:
                    ET_Sd = 0
                    HK_depth = []
                    opt_Sd = 0
                    Dtree_depth = []
                    nDtree_depth = []
                    max_dtree_depth = 0
                    max_hk_depth = 0
                    for v in output_set:
                        hk_d = tree_utils.toRoot(HK_active_occurrence_dict[v])
                        max_hk_depth = max(hk_d, max_hk_depth)
                        HK_depth.append(hk_d)

                        dtree_d = Dtree_utils.toRoot(Dtree[v])
                        Dtree_depth.append(dtree_d)
                        max_dtree_depth = max(max_dtree_depth, dtree_d)
                        #nDtree_depth.append(Dtree_utils.toRoot(nDtree[v]))
                        if isSmallGraph:
                            pass
                            # opt_Sd += Dtree_utils.toRoot(opt[v])
                            # ET_Sd += tree_utils.toRoot(ET_active_occurrence_dict[v])
                    print("HK: %d, Dtree: %d, nDtree: %d", len(HK_depth), len(Dtree_depth))
                    plt.hist(HK_depth, color = 'r', bins = np.linspace(0, max_dtree_depth, max(max_dtree_depth // 10, 10)), alpha = 0.75, label = 'HK')
                    plt.hist(Dtree_depth, color = 'g', bins = np.linspace(0, max_dtree_depth, max(max_dtree_depth // 10, 10)), alpha = 0.75, label = 'Dtree')
                    #plt.hist(nDtree_depth, color = 'b', bins = np.linspace(0, 499, 50), alpha = 0.75, label = 'nDtree')
                    plt.gca().set(title = "Frequence of depth", ylabel = "Frequence")
                    plt.legend()
                    plt.savefig(os.path.join("./res/depth/" + testcase, str(cc)))
                    plt.close()

        deleted_edges = set()
        if current_time in expiredDict:

            for (u, v) in expiredDict[current_time]:
                deleted_edges.add((u, v))
                del inserted_edge[(u, v)]
            del expiredDict[current_time]

        deletion_count += len(deleted_edges)

        # delete edges
        if len(deleted_edges) > 0:
            if testcase in ['osmswitzerland', 'TX']:
                continue

            for (a, b) in deleted_edges:

                # HK
                if (a, b) in HK_non_tree_edges:
                    HK_res.de_nte_count += 1
                    start = timer()
                    HKupdate.delete_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                    HK_res.de_nte_time += (timer() - start)
                else:
                    HK_res.de_te_count += 1
                    start = timer()
                    HKupdate.delete_tree_edge(a, b, HK_tree_edges, HK_non_tree_edges, HK_active_occurrence_dict,
                                        HK_tree_edges_pointers, max_priority)
                    HK_res.de_te_time += (timer() - start)

                # nDtree, naive Dtree
                if nDtree[a] in nDtree[b].nte or nDtree[b] in nDtree[a].nte:
                    nDtree_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils.delete_nte(nDtree[a], nDtree[b])
                    nDtree_res.de_nte_time += (timer() - start)
                else:
                    nDtree_res.de_te_count += 1
                    start = timer()
                    Dtree_utils.delete_te_simple(nDtree[a], nDtree[b])
                    nDtree_res.de_te_time += (timer() - start)

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in deletion")

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
                    if not (nDtree[a].parent == nDtree[b] or nDtree[b].parent == nDtree[a]) and \
                            not (nDtree[a] in nDtree[b].nte and nDtree[b] in nDtree[a].nte):
                        # inserting a non tree edge
                        nDtree_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in DT
                        start = timer()
                        Dtree_utils.insert_nte_simple(nDtree[a], nDtree[b])
                        nDtree_res.in_nte_time += (timer() - start + go_to_root_nDtree)

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in insertion")

                # Dtree
                if Dtree[a] in Dtree[b].nte or Dtree[b] in Dtree[a].nte:
                    Dtree_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils.delete_nte(Dtree[a], Dtree[b])
                    Dtree_res.de_nte_time += (timer() - start)
                else:
                    Dtree_res.de_te_count += 1
                    start = timer()
                    Dtree_utils.delete_te(Dtree[a], Dtree[b])
                    Dtree_res.de_te_time += (timer() - start)

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, HK_active_occurrence_dict):
                    raise ValueError("Error in deletion in Dtree")

                # remove isolated nodes from v_set.
                if Dtree[a].parent is None and Dtree[a].size == 1:
                    v_set.remove(a)
                    assert Dtree[a].size == nDtree[a].size
                if Dtree[b].parent is None and Dtree[b].size == 1:
                    v_set.remove(b)
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
                        raise ValueError("Error in insertion")

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

            # S_d
            ET_Sd = 0
            HK_depth = []
            opt_Sd = 0
            Dtree_depth = []
            nDtree_depth = []
            for v in output_set:
                HK_depth.append(tree_utils.toRoot(HK_active_occurrence_dict[v]))
                Dtree_depth.append(Dtree_utils.toRoot(Dtree[v]))
                nDtree_depth.append(Dtree_utils.toRoot(nDtree[v]))
                if isSmallGraph:
                    pass
                    #opt_Sd += Dtree_utils.toRoot(opt[v])
                    #ET_Sd += tree_utils.toRoot(ET_active_occurrence_dict[v])
        plt.hist(HK_depth, color = 'r', bins = np.linspace(0, 49, 50), alpha=0.75, label = 'HK')
        plt.hist(Dtree_depth, color='g', bins = np.linspace(0, 49, 50), alpha=0.75, label = 'Dtree')
        #plt.hist(nDtree_depth, color = 'b', bins = np.linspace(0, 49, 50), alpha = 0.75, label = 'nDtree')
        plt.yscale('log', nonposy = 'clip')
        plt.gca().set(title="Frequence of depth", ylabel="Frequence")
        plt.legend()
        plt.savefig(os.path.join("./res/depth/" + testcase, str(current_time)))
        plt.close()
