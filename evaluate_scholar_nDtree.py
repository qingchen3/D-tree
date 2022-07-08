import sys
from _collections import defaultdict
from utils import tree_utils
from utils.tree_utils import constructST_adjacency_list, readQueries
from Dtree import Dtree_utils
from Dtree.DTNode import DTNode
from timeit import default_timer as timer
from Class.Res import Res
from utils.IO import setup, printRes, output_average_dist_by_method, update_maintanence, update_res_query_Sd,\
    update_average_runtime, update_average_uneven_size_beta, update_average_distance, copyRes
from os.path import join, isfile
from os import listdir
from pathlib import Path


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

    _, nDtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)

    expiredDict = defaultdict(set)
    inserted_edge = defaultdict()
    nDtree_res = Res()
    nDtree_res_pre = Res()

    # distribution of distance between root and nodes
    nDtree_accumulated_dist = defaultdict(int)

    insertion_count = 0
    deletion_count = 0

    steps_DT_nte = 0

    #data_folder = './temp/'
    updates_folder = 'updates/scholar'
    #data_filenames = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
    current_time = start_timestamp
    v_set = set()
    edges_num = 0
    count_snapshot = 0

    nDtree_sum_small_size = 0
    nDtree_sum_beta = 0

    # while current_time <= end_timestamp + survival_time:
    while current_time <= test_points[-1]:
        # loop records and start with the record with current_time
        inserted_edges_current = set()
        if current_time <= end_timestamp + survival_time:
            #if str(current_time) in data_filenames:
            insertions_file = join(updates_folder, "%d_insertion" % current_time)
            if Path(insertions_file).exists():
                with open(insertions_file, 'r') as reader:
                    for line in reader.readlines():
                        items = line.rstrip().split()
                        a = int(items[0])
                        b = int(items[1])
                        v_set.add(a)
                        v_set.add(b)
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
                            edges_num += 1
                            nDtree_res.in_te_count += 1
                            start = timer()
                            Dtree_utils.insert_te_simple(nDtree[a], nDtree[b], root_a, root_b)
                            nDtree_res.in_te_time += (timer() - start + go_to_root_nDtree)
                        else:  # a and b are connected
                            # (a, b) is a new  non tree edge
                            #if not (nDtree[a].parent == nDtree[b] or nDtree[b].parent == nDtree[a]) and \
                            #        not (nDtree[a] in nDtree[b].nte and nDtree[b] in nDtree[a].nte):
                                # inserting a non tree edge
                            if not (nDtree[a].parent == nDtree[b] or nDtree[b].parent == nDtree[a]):
                                if not (nDtree[a] in nDtree[b].nte and nDtree[b] in nDtree[a].nte):
                                    edges_num += 1
                                nDtree_res.in_nte_count += 1

                                # count running time for inserting a non tree edge in DT
                                start = timer()
                                Dtree_utils.insert_nte_simple(nDtree[a], nDtree[b])
                                nDtree_res.in_nte_time += (timer() - start + go_to_root_nDtree)

            deletions_file = join(updates_folder, "%d_deletion" % current_time)
            if Path(deletions_file).exists():
                with open(deletions_file, 'r') as reader:
                    for line in reader.readlines():
                        items = line.rstrip().split()
                        a = int(items[0])
                        b = int(items[1])
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

                        # remove isolated nodes from v_set.
                        if nDtree[a].parent is None and nDtree[a].size == 1:
                            v_set.remove(a)
                        if nDtree[b].parent is None and nDtree[b].size == 1:
                            v_set.remove(b)

        current_time += 1
        if current_time in test_points:
            # output to terminal
            print("timestamp:%d" % current_time)
            insertion_nte_data = list()
            insertion_nte_data.append(["nDtree", nDtree_res.in_nte_count, nDtree_res.in_nte_time])
            printRes("inserting non tree edge", insertion_nte_data)
            print()

            insertion_te_data = list()
            insertion_te_data.append(["nDtree", nDtree_res.in_te_count, nDtree_res.in_te_time])
            printRes("inserting tree edge", insertion_te_data)
            print()

            deletion_nte_data = list()
            deletion_nte_data.append(["nDtree", nDtree_res.de_nte_count, nDtree_res.de_nte_time])
            printRes("deleting non tree edge", deletion_nte_data)
            print()

            deletion_te_data = list()
            deletion_te_data.append(["nDtree", nDtree_res.de_te_count, nDtree_res.de_te_time])
            printRes("deleting tree edge", deletion_te_data)
            print()

            # evaluate query performance
            test_queries = readQueries(testcase, current_time)

            query_count = 0
            start = timer()
            for (x, y) in test_queries:
                if x not in nDtree or y not in nDtree:
                    continue
                Dtree_utils.query(nDtree[x], nDtree[y])
                query_count += 1
                if query_count == 50000000:
                    break
            query_nDtree = timer() - start
            query_data = []
            query_data.append(["nDtree", str(query_count), query_nDtree])
            printRes("connectivity query", query_data)

            update_res_query_Sd(testcase, 'query', [current_time, query_nDtree], 'nDtree')

            del test_queries

            # S_d
            nDtree_Sd = 0
            reader = open('vertices/%s/%d' % (testcase, current_time))
            v_count = 0
            for line in reader.readlines():
                v = int(line.rstrip())
                if v not in nDtree:
                    continue
                v_count += 1
                d_v = Dtree_utils.toRoot(nDtree[v])
                nDtree_Sd += d_v
                nDtree_accumulated_dist[d_v] += 1
            update_res_query_Sd(testcase, 'Sd', [current_time, nDtree_Sd], 'nDtree')

            # output to terminal
            Sd_data = list()
            Sd_data.append(["nDtree", "", nDtree_Sd])
            printRes("S_d", Sd_data)

            print(current_time, ":", "%d vertices" % v_count, "%d queries" % query_count)
            # output to terminal
            print()

            update_average_uneven_size_beta(testcase, 'uneven', [current_time,
                                            nDtree_sum_small_size/(nDtree_res.de_te_count + 0.000001)], 'nDtree')

            update_average_uneven_size_beta(testcase, 'beta', [current_time,
                                            nDtree_sum_beta/(nDtree_res.de_te_count + 0.000001)], 'nDtree')

            update_average_distance(testcase, [current_time, nDtree_Sd / (len(v_set) + 0.000001)], 'nDtree')

            # maintenance performance for large graphs
            update_maintanence(testcase, nDtree_res, 'nDtree')

            # inserting tree edges
            update_average_runtime(testcase,
                                   "insertion_te",
                                   [current_time, (nDtree_res.in_te_time - nDtree_res_pre.in_te_time) /
                                    (nDtree_res.in_te_count - nDtree_res_pre.in_te_count + 0.00001)], 'nDtree')

            # inserting non-tree edges
            update_average_runtime(testcase,
                                   "insertion_nte",
                                   [current_time, (nDtree_res.in_nte_time - nDtree_res_pre.in_nte_time) /
                                    (nDtree_res.in_nte_count - nDtree_res_pre.in_nte_count + 0.00001)], 'nDtree')

            # deleting tree edges
            update_average_runtime(testcase,
                                   "deletion_te",
                                   [current_time, (nDtree_res.de_te_time - nDtree_res_pre.de_te_time) /
                                    (nDtree_res.de_te_count - nDtree_res_pre.de_te_count + 0.00001)], 'nDtree')

            # deleting non-tree edges
            update_average_runtime(testcase,
                                   "deletion_nte",
                                   [current_time, (nDtree_res.de_nte_time - nDtree_res_pre.de_nte_time) /
                                    (nDtree_res.de_nte_count - nDtree_res_pre.de_nte_count + 0.00001)], 'nDtree')
            copyRes(nDtree_res, nDtree_res_pre)

            # output distributions of average distances between nodes and roots
            #count = len(test_points) # number of snapshots
            count_snapshot += 1  # number of snapshots
            #output_average_dist(distance_data, count, testcase, isSmallGraph)
            output_average_dist_by_method(nDtree_accumulated_dist, count_snapshot, testcase, 'nDtree')




