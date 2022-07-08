import sys
from _collections import defaultdict
from utils.tree_utils import constructST_adjacency_list, readQueries
from timeit import default_timer as timer
from Class.Res import Res
from utils.IO import setup, printRes, output_average_dist_by_method, update_maintanence, update_res_query_Sd
from os.path import join, isfile
from os import listdir
from pathlib import Path
from HK import HK_utils
from HK.HKNode import HKNode
import HK.updates as HKupdate
import random
from utils import tree_utils


if __name__ == '__main__':
    sys.setrecursionlimit(50000000)
    testcase = sys.argv[1]
    #if testcase != 'scholar':
    #    raise ValueError("filename has to be scholar.")

    # setup starting point and ending point
    start_timestamp = 1919
    end_timestamp = 2022

    #  setups
    survival_time, test_points = setup(testcase, start_timestamp, end_timestamp)
    sanity_check = False  # True: switch on the sanity check; False: swith off the sanity check.

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

    HK_forest, HK_tree_edges, HK_non_tree_edges, HK_active_occurrence_dict, HK_tree_edges_pointers = \
        HK_utils.HK_constructSF(graph, 0, max_priority)

    inserted_edge = defaultdict()
    HK_res = Res()

    # distribution of distance between root and nodes
    HK_accumulated_dist = defaultdict(int)

    insertion_count = 0
    deletion_count = 0

    steps_DT_nte = 0

    data_folder = './temp/'
    updates_folder = './res/updates/scholar'
    data_filenames = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
    current_time = start_timestamp
    v_set = set()
    count_snapshot = 0
    while current_time <= end_timestamp + survival_time:
        # loop records and start with the record with current_time
        if current_time <= end_timestamp + survival_time:
            #if str(current_time) in data_filenames:
            insertions_file = join(updates_folder, "%d_insertion" % current_time)
            if Path(insertions_file).exists():
                with open(insertions_file, 'r') as reader:
                    for line in reader.readlines():
                        items = line.rstrip().split()
                        a = int(items[0])
                        b = int(items[1])

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
                            HKupdate.insert_tree_edge(a, root_a, b, root_b, HK_tree_edges,
                                                      HK_active_occurrence_dict,
                                                      HK_tree_edges_pointers, max_priority)
                            HK_res.in_te_time += (timer() - start + go_to_root_HK)

                        else:  # a and b are connected
                            #if (a, b) not in HK_tree_edges and (a, b) not in HK_non_tree_edges:  # (a, b) is a new  non-tree edge
                            if (a, b) not in HK_tree_edges:
                                continue

                            HK_res.in_nte_count += 1

                            # count running time for inserting a non tree edge in HK
                            start = timer()
                            HKupdate.insert_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                            HK_res.in_nte_time += (timer() - start + go_to_root_HK)

            deletions_file = join(updates_folder, "%d_deletion" % current_time)
            if Path(deletions_file).exists():
                with open(deletions_file, 'r') as reader:
                    for line in reader.readlines():
                        items = line.rstrip().split()
                        a = int(items[0])
                        b = int(items[1])
                        # HK
                        if (a, b) in HK_non_tree_edges:
                            HK_res.de_nte_count += 1
                            start = timer()
                            HKupdate.delete_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)
                            HK_res.de_nte_time += (timer() - start)
                        else:
                            HK_res.de_te_count += 1
                            start = timer()
                            HKupdate.delete_tree_edge(a, b, HK_tree_edges, HK_non_tree_edges,
                                                      HK_active_occurrence_dict,
                                                      HK_tree_edges_pointers, max_priority)
                            HK_res.de_te_time += (timer() - start)

        current_time += 1
        if current_time in test_points:
            # output to terminal
            print("timestamp:%d" % current_time)
            insertion_nte_data = list()
            insertion_nte_data.append(["HK", HK_res.in_nte_count, HK_res.in_nte_time])
            printRes("inserting non tree edge", insertion_nte_data)
            print()

            insertion_te_data = list()
            insertion_te_data.append(["HK", HK_res.in_te_count, HK_res.in_te_time])
            printRes("inserting tree edge", insertion_te_data)
            print()

            deletion_nte_data = list()
            deletion_nte_data.append(["HK", HK_res.de_nte_count, HK_res.de_nte_time])
            printRes("deleting non tree edge", deletion_nte_data)
            print()

            deletion_te_data = list()
            deletion_te_data.append(["HK", HK_res.de_te_count, HK_res.de_te_time])
            printRes("deleting tree edge", deletion_te_data)
            print()

            # evaluate query performance
            test_queries = readQueries(testcase, current_time)

            query_count = 0
            start = timer()
            for (x, y) in test_queries:
                if x not in HK_active_occurrence_dict or y not in HK_active_occurrence_dict:
                    continue
                tree_utils.query(x, y, HK_active_occurrence_dict)
                query_count += 1
                if query_count == 50000000:
                    break
            query_HK = timer() - start

            query_data = []
            query_data.append(["HK", str(query_count), query_HK])
            printRes("connectivity query", query_data)

            update_res_query_Sd(testcase, 'query', [current_time, query_HK], 'HK')

            del test_queries

            # S_d
            HK_Sd = 0
            reader = open('res/vertices/%s/%d' % (testcase, current_time))
            v_count = 0
            for line in reader.readlines():
                v = int(line.rstrip())
                if v not in HK_active_occurrence_dict:
                    continue
                v_count += 1
                d_v = tree_utils.toRoot(HK_active_occurrence_dict[v])
                HK_Sd += d_v
                HK_accumulated_dist[d_v] += 1
            update_res_query_Sd(testcase, 'Sd', [current_time, HK_Sd], 'HK')

            # output to terminal
            Sd_data = list()
            Sd_data.append(["HK", "", HK_Sd])
            printRes("S_d", Sd_data)

            print(current_time, ":", "%d vertices" % v_count, "%d queries" % query_count)
            # output to terminal
            print()

            # maintenance performance for large graphs
            update_maintanence(testcase, HK_res, 'HK')
            #if not isSmallGraph:
            #    output_data = []
            #    output_data.append(Dtree_res)
            #    if isSmallGraph:
            #        updateRes(testcase, output_data)

            # distance data
            #distance_data = []
            #distance_data.append(Dtree_accumulated_dist)

            # output distributions of average distances between nodes and roots
            #count = len(test_points) # number of snapshots
            count_snapshot += 1  # number of snapshots
            #output_average_dist(distance_data, count, testcase, isSmallGraph)
            output_average_dist_by_method(HK_accumulated_dist, count_snapshot, testcase, 'HK')




