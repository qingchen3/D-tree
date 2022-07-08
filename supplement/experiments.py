import os, sys
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import random
from _collections import defaultdict
from utils import tree_utils
from utils.tree_utils import constructST_adjacency_list
from utils.graph_utils import loadGraph
from utils.graph_utils import best_BFS

from Dtree import Dtree_utils
from ET.ETNode import ETNode
from Dtree.DTNode import DTNode
from HK.HKNode import HKNode
from timeit import default_timer as timer

import ET.ET_utils as ET_utils
import HK.HK_utils as HK_utils

import HK.updates as HKupdate
import ET.updates as ETupdate

from Class.Res import Res
from utils.IO import setup, printRes
from utils.graph_utils import order
from utils.tree_utils import generatePairs


def excludeET(testcase):
    sys.setrecursionlimit(50000000)
    if testcase not in ['stackoverflow', 'youtube', 'dblp']: 
        raise ValueError("try 'stackoverflow', 'youtube' and 'dblp' data sets ")
    records = loadGraph(testcase)

    # setup starting point and ending point
    start_timestamp = records[0][2]
    end_timestamp = records[-1][2]

    #  setups
    survival_time, test_points, query_writer, Sd_writer = setup(testcase, start_timestamp, end_timestamp)
    n = 100000000

    sanity_check = True

    idx = 0
    max_priority = sys.maxsize
    graph = defaultdict(set)

    print(survival_time, "%d tests, first test: %d, last test: %d" %(len(test_points), test_points[0], test_points[-1]))
    print(start_timestamp, end_timestamp)

    # spanningtree, n, nte_per_vertex = baseline.initialize(graph, n)
    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)

    _, nDtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    rnd_forest, ET_tree_edges, ET_non_tree_edges, ET_active_occurrence_dict, ET_tree_edges_pointers = \
        ET_utils.ET_constructSF(graph, 0, max_priority)
    HK_forest, HK_tree_edges, HK_non_tree_edges, HK_active_occurrence_dict, HK_tree_edges_pointers = \
        HK_utils.HK_constructSF(graph, 0, max_priority)

    expiredDict = defaultdict(set)
    inserted_edge = defaultdict()

    ET_res = Res()
    HK_res = Res()
    nDtree_res = Res()
    Dtree_res = Res()

    insertion_count = 0
    deletion_count = 0

    v_set = set()

    current_time = start_timestamp
    while current_time <= end_timestamp + survival_time:
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

            for (a, b) in inserted_edges:
                graph[a].add(b)
                graph[b].add(a)

                # initialize ET Node if not exists
                if a not in ET_active_occurrence_dict:
                    node = ETNode(a, random.randint(1, max_priority))
                    node.active = True
                    ET_active_occurrence_dict[a] = node
                if b not in ET_active_occurrence_dict:
                    node = ETNode(b, random.randint(1, max_priority))
                    node.active = True
                    ET_active_occurrence_dict[b] = node

                # ET
                start = timer()
                root_a, distance_a = tree_utils.find_root_with_steps(ET_active_occurrence_dict[a])
                root_b, distance_b = tree_utils.find_root_with_steps(ET_active_occurrence_dict[b])
                go_to_root_ET = timer() - start

                if root_a.val != root_b.val:
                    ET_res.in_te_count += 1
                    start = timer()
                    new_root = ETupdate.insert_tree_edge(a, root_a, b, root_b, ET_tree_edges,
                                                   ET_active_occurrence_dict,
                                                   ET_tree_edges_pointers, max_priority)
                    ET_res.in_te_time += (timer() - start + go_to_root_ET)

                else:  # a and b are connected
                    if (a, b) not in ET_tree_edges and (
                            a, b) not in ET_non_tree_edges:  # (a, b) is a new  non tree edge

                        ET_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in ET
                        start = timer()
                        steps = ETupdate.insert_nontree_edge(a, b, ET_active_occurrence_dict, ET_non_tree_edges)
                        ET_res.in_nte_time += (timer() - start + go_to_root_ET)

                # initialize ETNode for HK if not exists
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

                # HK
                start = timer()
                root_a, distance_a = tree_utils.find_root_with_steps(HK_active_occurrence_dict[a])
                root_b, distance_b = tree_utils.find_root_with_steps(HK_active_occurrence_dict[b])
                go_to_root_HK = timer() - start

                if root_a.val != root_b.val:
                    HK_res.in_te_count += 1
                    start = timer()
                    new_root = HKupdate.insert_tree_edge(a, root_a, b, root_b, HK_tree_edges, HK_active_occurrence_dict,
                                                    HK_tree_edges_pointers, max_priority)
                    HK_res.in_te_time += (timer() - start + go_to_root_HK)

                else:  # a and b are connected
                    if (a, b) not in HK_tree_edges and (a, b) not in HK_non_tree_edges:  # (a, b) is a new  non tree edge

                        HK_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in ET
                        start = timer()
                        steps = HKupdate.insert_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                        HK_res.in_nte_time += (timer() - start + go_to_root_HK)

                if sanity_check and tree_utils.query(a, b, HK_active_occurrence_dict) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in insertion in HK")

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

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in insertion")

                # Dtree, Dtree with heuristics and balancing
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
                            not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[
                                a].nte):
                        # inserting a non tree edge
                        Dtree_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in DT
                        start = timer()
                        Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
                        Dtree_res.in_nte_time += (timer() - start + go_to_root_Dtree)

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in insertion")


        deleted_edges = set()
        if current_time in expiredDict:

            for (u, v) in expiredDict[current_time]:
                deleted_edges.add((u, v))
                del inserted_edge[(u, v)]
            del expiredDict[current_time]

        deletion_count += len(deleted_edges)

        if len(deleted_edges) > 0:
            for (a, b) in deleted_edges:
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

                if sanity_check and tree_utils.query(a, b, HK_active_occurrence_dict) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in deletion in HK")

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

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
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
                    Dtree_utils.delete_te(Dtree[a], Dtree[b])
                    Dtree_res.de_te_time += (timer() - start)

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in deletion in Dtree")

                # remove isolated nodes.
                if Dtree[a].parent is None and Dtree[a].size == 1:
                    v_set.remove(a)
                    assert Dtree[a].size == nDtree[a].size
                if Dtree[b].parent is None and Dtree[b].size == 1:
                    v_set.remove(b)
                    assert Dtree[b].size == nDtree[b].size


        current_time += 1
        if current_time in test_points:
            print(current_time)
            insertion_nte_data = []
            insertion_nte_data.append(["nDtree", nDtree_res.in_nte_count, nDtree_res.in_nte_time])
            insertion_nte_data.append(["Dtree", Dtree_res.in_nte_count, Dtree_res.in_nte_time])
            insertion_nte_data.append(["HK", HK_res.in_nte_count, HK_res.in_nte_time])
            insertion_nte_data.append(["ET", ET_res.in_nte_count, ET_res.in_nte_time])
            printRes("inserting non tree edge", insertion_nte_data)
            print()

            insertion_te_data = []
            insertion_te_data.append(["nDtree", nDtree_res.in_te_count, nDtree_res.in_te_time])
            insertion_te_data.append(["Dtree", Dtree_res.in_te_count, Dtree_res.in_te_time])
            insertion_te_data.append(["HK", HK_res.in_te_count, HK_res.in_te_time])
            insertion_te_data.append(["ET", ET_res.in_te_count, ET_res.in_te_time])

            printRes("inserting tree edge", insertion_te_data)
            print()

            deletion_nte_data = []
            deletion_nte_data.append(["nDtree", nDtree_res.de_nte_count, nDtree_res.de_nte_time])
            deletion_nte_data.append(["Dtree", Dtree_res.de_nte_count, Dtree_res.de_nte_time])
            deletion_nte_data.append(["HK", HK_res.de_nte_count, HK_res.de_nte_time])
            deletion_nte_data.append(["ET", ET_res.de_nte_count, ET_res.de_nte_time])

            printRes("deleting non tree edge", deletion_nte_data)
            print()

            deletion_te_data = []
            deletion_te_data.append(["nDtree", nDtree_res.de_te_count, nDtree_res.de_te_time])
            deletion_te_data.append(["Dtree", Dtree_res.de_te_count, Dtree_res.de_te_time])
            deletion_te_data.append(["HK", HK_res.de_te_count, HK_res.de_te_time])
            deletion_te_data.append(["ET", ET_res.de_te_count, ET_res.de_te_time])

            printRes("deleting tree edge", deletion_te_data)
            print()

            v_list = list(v_set)
            test_edges = generatePairs(v_list)
            print('number of tests:', len(test_edges))

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

            start = timer()
            for (x, y) in test_edges:
                tree_utils.query(x, y, ET_active_occurrence_dict)
            query_ET = timer() - start


            query_output_text = "samples"

            query_data = []
            query_data.append(["nDtree", query_output_text, query_nDtree])
            query_data.append(["Dtree", query_output_text, query_Dtree])
            query_data.append(["HK", query_output_text, query_HK])
            query_data.append(["ET", query_output_text, query_ET])



            printRes("connectivity query", query_data)


def excludeOPT(testcase):
    sys.setrecursionlimit(50000000)

    if testcase != 'stackoverflow':
        raise ValueError("file name is not stackoverflow")
    records = loadGraph(testcase)


    # setup starting point and ending point
    start_timestamp = records[0][2]
    end_timestamp = records[-1][2]


    # setups
    survival_time, test_points, query_writer, Sd_writer = setup(testcase, start_timestamp, end_timestamp)
    n = 100000000
    # disable writers
    insertion_writer = None
    deletion_writer = None
    query_writer = None


    sanity_check = True

    idx = 0
    max_priority = sys.maxsize
    graph = defaultdict(set)

    print(survival_time, "%d tests, first test: %d, last test: %d" %(len(test_points), test_points[0], test_points[-1]))
    print(start_timestamp, end_timestamp)

    # spanningtree, n, nte_per_vertex = baseline.initialize(graph, n)
    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)

    _, nDtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    rnd_forest, ET_tree_edges, ET_non_tree_edges, ET_active_occurrence_dict, ET_tree_edges_pointers = \
        ET_utils.ET_constructSF(graph, 0, max_priority)
    HK_forest, HK_tree_edges, HK_non_tree_edges, HK_active_occurrence_dict, HK_tree_edges_pointers = \
        HK_utils.HK_constructSF(graph, 0, max_priority)
    _, opt = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)

    expiredDict = defaultdict(set)
    inserted_edge = defaultdict()

    ET_res = Res()
    HK_res = Res()
    nDtree_res = Res()
    Dtree_res = Res()
    opt_res = Res()

    insertion_count = 0
    deletion_count = 0

    v_set = set()

    current_time = start_timestamp
    while current_time <= end_timestamp + survival_time:
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

            for (a, b) in inserted_edges:
                graph[a].add(b)
                graph[b].add(a)

                # initialize ET Node if not exists
                if a not in ET_active_occurrence_dict:
                    node = ETNode(a, random.randint(1, max_priority))
                    node.active = True
                    ET_active_occurrence_dict[a] = node
                if b not in ET_active_occurrence_dict:
                    node = ETNode(b, random.randint(1, max_priority))
                    node.active = True
                    ET_active_occurrence_dict[b] = node

                # ET
                start = timer()
                root_a, distance_a = tree_utils.find_root_with_steps(ET_active_occurrence_dict[a])
                root_b, distance_b = tree_utils.find_root_with_steps(ET_active_occurrence_dict[b])
                go_to_root_ET = timer() - start

                if root_a.val != root_b.val:
                    ET_res.in_te_count += 1
                    start = timer()
                    new_root = ETupdate.insert_tree_edge(a, root_a, b, root_b, ET_tree_edges,
                                                   ET_active_occurrence_dict,
                                                   ET_tree_edges_pointers, max_priority)
                    ET_res.in_te_time += (timer() - start + go_to_root_ET)

                else:  # a and b are connected
                    if (a, b) not in ET_tree_edges and (
                            a, b) not in ET_non_tree_edges:  # (a, b) is a new  non tree edge

                        ET_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in ET
                        start = timer()
                        steps = ETupdate.insert_nontree_edge(a, b, ET_active_occurrence_dict, ET_non_tree_edges)
                        ET_res.in_nte_time += (timer() - start + go_to_root_ET)

                # initialize ETNode for HK if not exists
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

                # HK
                start = timer()
                root_a, distance_a = tree_utils.find_root_with_steps(HK_active_occurrence_dict[a])
                root_b, distance_b = tree_utils.find_root_with_steps(HK_active_occurrence_dict[b])
                go_to_root_HK = timer() - start

                if root_a.val != root_b.val:
                    HK_res.in_te_count += 1
                    start = timer()
                    new_root = HKupdate.insert_tree_edge(a, root_a, b, root_b, HK_tree_edges, HK_active_occurrence_dict,
                                                    HK_tree_edges_pointers, max_priority)
                    HK_res.in_te_time += (timer() - start + go_to_root_HK)

                else:  # a and b are connected
                    if (a, b) not in HK_tree_edges and (a, b) not in HK_non_tree_edges:  # (a, b) is a new  non tree edge

                        HK_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in ET
                        start = timer()
                        steps = HKupdate.insert_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                        HK_res.in_nte_time += (timer() - start + go_to_root_HK)

                if sanity_check and tree_utils.query(a, b, HK_active_occurrence_dict) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in insertion in HK")

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

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in insertion")

                # Dtree, Dtree with heuristics and balancing
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
                            not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[
                                a].nte):
                        # inserting a non tree edge
                        Dtree_res.in_nte_count += 1

                        # count running time for inserting a non tree edge in DT
                        start = timer()
                        Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
                        Dtree_res.in_nte_time += (timer() - start + go_to_root_Dtree)

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in insertion")

                # opt

                graph[a].add(b)
                graph[b].add(a)
                # opt that give 2-approximation
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
                            not (opt[a] in opt[b].nte and opt[b] in opt[
                                a].nte):
                        opt_res.in_nte_count += 1

                        start = timer()
                        target = best_BFS(graph, n, a)  # find the best BFS-tree
                        Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set())

                        # if target != root_a.val: # reconstruct the BFS tree
                        #   BFStree_utils.reconstruct_BFS_tree(opt[target], opt, set())
                        opt[a].nte.add(opt[b])
                        opt[b].nte.add(opt[a])
                        opt_res.in_nte_time += (timer() - start + go_to_root_opt)
                if sanity_check and Dtree_utils.query_simple(opt[a], opt[b]) != tree_utils.query(a, b,
                                                                                                       ET_active_occurrence_dict):
                    raise ValueError("Error in insertion")

        deleted_edges = set()
        if current_time in expiredDict:

            for (u, v) in expiredDict[current_time]:
                deleted_edges.add((u, v))
                del inserted_edge[(u, v)]
            del expiredDict[current_time]

        deletion_count += len(deleted_edges)

        if len(deleted_edges) > 0:
            for (a, b) in deleted_edges:
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

                if sanity_check and tree_utils.query(a, b, HK_active_occurrence_dict) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in deletion in HK")

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

                if sanity_check and Dtree_utils.query_simple(nDtree[a], nDtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
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
                    Dtree_utils.delete_te(Dtree[a], Dtree[b])
                    Dtree_res.de_te_time += (timer() - start)

                if sanity_check and Dtree_utils.query_simple(Dtree[a], Dtree[b]) != tree_utils.query(a, b, ET_active_occurrence_dict):
                    raise ValueError("Error in deletion in Dtree")

                # remove isolated nodes.
                if Dtree[a].parent is None and Dtree[a].size == 1:
                    v_set.remove(a)
                    assert Dtree[a].size == nDtree[a].size
                if Dtree[b].parent is None and Dtree[b].size == 1:
                    v_set.remove(b)
                    assert Dtree[b].size == nDtree[b].size


                graph[a].remove(b)
                graph[b].remove(a)
                # DT-BFS
                if opt[a] in opt[b].nte or opt[b] in opt[a].nte:
                    opt_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils.delete_nte(opt[a], opt[b])

                    target = best_BFS(graph, n, a)  # find the best BFS-tree
                    Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set())
                    opt_res.de_nte_time += (timer() - start)
                else:
                    opt_res.de_te_count += 1
                    start = timer()
                    res = Dtree_utils.delete_te(opt[a], opt[b])
                    if type(res) is tuple: # delete tree edge (a, b) splits a spanning tree
                        target_a = best_BFS(graph, n, a)  # find root of the best BFS-tree contains a
                        target_b = best_BFS(graph, n, b)  # find root of the best BFS-tree contain b
                        Dtree_utils.reconstruct_BFS_tree(opt[target_a], opt, set())
                        Dtree_utils.reconstruct_BFS_tree(opt[target_b], opt, set())
                    else:
                        target = best_BFS(graph, n, a)  # find the best BFS-tree
                        Dtree_utils.reconstruct_BFS_tree(opt[target], opt, set())
                    opt_res.de_te_time += (timer() - start)

                if sanity_check and Dtree_utils.query_simple(opt[a], opt[b]) != tree_utils.query(a, b,
                                                                                                       ET_active_occurrence_dict):
                    raise ValueError("Error in insertion")

        current_time += 1
        if insertion_count > 100 and insertion_count % 10 == 0:  # output results after 100 insertions of edges
            print(current_time)
            insertion_nte_data = []
            insertion_nte_data.append(["nDtree", nDtree_res.in_nte_count, nDtree_res.in_nte_time])
            insertion_nte_data.append(["Dtree", Dtree_res.in_nte_count, Dtree_res.in_nte_time])
            insertion_nte_data.append(["HK", HK_res.in_nte_count, HK_res.in_nte_time])
            insertion_nte_data.append(["ET", ET_res.in_nte_count, ET_res.in_nte_time])
            insertion_nte_data.append(["opt", opt_res.in_nte_count, opt_res.in_nte_time])
            printRes("inserting non tree edge", insertion_nte_data)
            print()

            insertion_te_data = []
            insertion_te_data.append(["nDtree", nDtree_res.in_te_count, nDtree_res.in_te_time])
            insertion_te_data.append(["Dtree", Dtree_res.in_te_count, Dtree_res.in_te_time])
            insertion_te_data.append(["HK", HK_res.in_te_count, HK_res.in_te_time])
            insertion_te_data.append(["ET", ET_res.in_te_count, ET_res.in_te_time])
            insertion_te_data.append(["opt", opt_res.in_te_count, opt_res.in_te_time])
            printRes("inserting tree edge", insertion_te_data)
            print()

            deletion_nte_data = []
            deletion_nte_data.append(["nDtree", nDtree_res.de_nte_count, nDtree_res.de_nte_time])
            deletion_nte_data.append(["Dtree", Dtree_res.de_nte_count, Dtree_res.de_nte_time])
            deletion_nte_data.append(["HK", HK_res.de_nte_count, HK_res.de_nte_time])
            deletion_nte_data.append(["ET", ET_res.de_nte_count, ET_res.de_nte_time])
            deletion_nte_data.append(["opt", opt_res.de_nte_count, opt_res.de_nte_time])
            printRes("deleting non tree edge", deletion_nte_data)
            print()

            deletion_te_data = []
            deletion_te_data.append(["nDtree", nDtree_res.de_te_count, nDtree_res.de_te_time])
            deletion_te_data.append(["Dtree", Dtree_res.de_te_count, Dtree_res.de_te_time])
            deletion_te_data.append(["HK", HK_res.de_te_count, HK_res.de_te_time])
            deletion_te_data.append(["ET", ET_res.de_te_count, ET_res.de_te_time])
            deletion_te_data.append(["opt", opt_res.de_te_count, opt_res.de_te_time])
            printRes("deleting tree edge", deletion_te_data)
            print()

            v_list = list(v_set)
            test_edges = generatePairs(v_list)
            print('number of tests:', len(test_edges))

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

            start = timer()
            for (x, y) in test_edges:
                tree_utils.query(x, y, ET_active_occurrence_dict)
            query_ET = timer() - start

            start = timer()
            for (x, y) in test_edges:
                Dtree_utils.query_simple(opt[x], opt[y])
            query_opt = timer() - start

            query_output_text = "samples"

            query_data = []
            query_data.append(["nDtree", query_output_text, query_nDtree])
            query_data.append(["Dtree", query_output_text, query_Dtree])
            query_data.append(["HK", query_output_text, query_HK])
            query_data.append(["ET", query_output_text, query_ET])
            query_data.append(["opt", query_output_text, query_opt])


            printRes("connectivity query", query_data)
