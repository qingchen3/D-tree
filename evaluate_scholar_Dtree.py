import sys
from _collections import defaultdict
from utils import tree_utils
from utils.tree_utils import constructST_adjacency_list, readQueries
from Dtree import Dtree_utils
from Dtree.DTNode import DTNode
from timeit import default_timer as timer
from Class.Res import Res
from utils.IO import setup, printRes, output_average_dist_by_method, update_maintanence, update_res_query_Sd, \
    update_average_runtime, update_res_vertices_edges, update_average_uneven_size_beta, update_average_distance, \
    copyRes
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
    # idx = 0
    max_priority = sys.maxsize
    graph = defaultdict(set)
    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)

    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)

    expiredDict = defaultdict(set)
    inserted_edge = defaultdict()
    Dtree_res = Res()
    Dtree_res_pre = Res()

    # distribution of distance between root and nodes
    Dtree_accumulated_dist = defaultdict(int)

    insertion_count = 0
    deletion_count = 0

    steps_DT_nte = 0

    #data_folder = './temp/'
    updates_folder = 'updates/scholar'
    #data_filenames = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
    current_time = start_timestamp
    v_set = set()
    count_snapshot = 0
    edges_num = 0

    Dtree_sum_small_size = 0
    Dtree_sum_beta = 0

    #while current_time <= end_timestamp + survival_time:
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
                            #if not (Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]) and \
                            #        not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[a].nte):
                            # inserting a non tree edge
                            if not (Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]):
                                if not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[a].nte):
                                    edges_num += 1

                                Dtree_res.in_nte_count += 1

                                # count running time for inserting a non tree edge in DT
                                start = timer()
                                Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
                                Dtree_res.in_nte_time += (timer() - start + go_to_root_Dtree)

            deletions_file = join(updates_folder, "%d_deletion" % current_time)
            if Path(deletions_file).exists():
                with open(deletions_file, 'r') as reader:
                    for line in reader.readlines():
                        items = line.rstrip().split()
                        a = int(items[0])
                        b = int(items[1])
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
                        edges_num -= 1
                        # remove isolated nodes from v_set.
                        if Dtree[a].parent is None and Dtree[a].size == 1:
                            v_set.remove(a)
                        if Dtree[b].parent is None and Dtree[b].size == 1:
                            v_set.remove(b)

        current_time += 1
        if current_time in test_points:
            # output to terminal
            print("timestamp:%d" % current_time)
            insertion_nte_data = list()
            insertion_nte_data.append(["Dtree", Dtree_res.in_nte_count, Dtree_res.in_nte_time])
            printRes("inserting non tree edge", insertion_nte_data)
            print()

            insertion_te_data = list()
            insertion_te_data.append(["Dtree", Dtree_res.in_te_count, Dtree_res.in_te_time])
            printRes("inserting tree edge", insertion_te_data)
            print()

            deletion_nte_data = list()
            deletion_nte_data.append(["Dtree", Dtree_res.de_nte_count, Dtree_res.de_nte_time])
            printRes("deleting non tree edge", deletion_nte_data)
            print()

            deletion_te_data = list()
            deletion_te_data.append(["Dtree", Dtree_res.de_te_count, Dtree_res.de_te_time])
            printRes("deleting tree edge", deletion_te_data)
            print()

            # evaluate query performance
            test_queries = readQueries(testcase, current_time)

            query_count = 0
            start = timer()
            for (x, y) in test_queries:
                if x not in Dtree or y not in Dtree:
                    continue
                Dtree_utils.query(Dtree[x], Dtree[y])
                query_count += 1
                if query_count == 50000000:
                    break
            query_Dtree = timer() - start
            query_data = []
            query_data.append(["Dtree", str(query_count), query_Dtree])
            printRes("connectivity query", query_data)

            update_res_query_Sd(testcase, 'query', [current_time, query_Dtree], 'Dtree')

            del test_queries

            # S_d
            Dtree_Sd = 0
            reader = open('vertices/%s/%d' % (testcase, current_time))
            v_count = 0
            for line in reader.readlines():
                v = int(line.rstrip())
                if v not in Dtree:
                    continue
                v_count += 1
                d_v = Dtree_utils.toRoot(Dtree[v])
                Dtree_Sd += d_v
                Dtree_accumulated_dist[d_v] += 1
            update_res_query_Sd(testcase, 'Sd', [current_time, Dtree_Sd], 'Dtree')

            # output to terminal
            Sd_data = list()
            Sd_data.append(["Dtree", "", Dtree_Sd])
            printRes("S_d", Sd_data)

            print(current_time, ":", "%d vertices" % v_count, "%d queries" % query_count)
            # output to terminal
            print()

            update_res_vertices_edges(testcase, 'vertices', [current_time, len(v_set)])
            update_res_vertices_edges(testcase, 'edges', [current_time, edges_num])

            update_average_uneven_size_beta(testcase, 'uneven', [current_time,
                                            Dtree_sum_small_size/(Dtree_res.de_te_count + 0.000001)], 'Dtree')

            update_average_uneven_size_beta(testcase, 'beta', [current_time,
                                            Dtree_sum_beta/(Dtree_res.de_te_count + 0.000001)], 'Dtree')

            update_average_distance(testcase, [current_time, Dtree_Sd / (len(v_set) + 0.000001)], 'Dtree')

            # maintenance performance for large graphs
            update_maintanence(testcase, Dtree_res, 'Dtree')

            # inserting tree edges
            #update_average_runtime(testcase, "insertion_te", [current_time,
            #                        Dtree_res.in_te_time / (Dtree_res.in_te_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "insertion_te",
                                   [current_time, (Dtree_res.in_te_time - Dtree_res_pre.in_te_time) /
                                    (Dtree_res.in_te_count - Dtree_res_pre.in_te_count + 0.00001)], 'Dtree')

            # inserting non-tree edges
            #update_average_runtime(testcase, "insertion_nte", [current_time,
            #                        Dtree_res.in_nte_time / (Dtree_res.in_nte_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "insertion_nte",
                                   [current_time, (Dtree_res.in_nte_time - Dtree_res_pre.in_nte_time) /
                                    (Dtree_res.in_nte_count - Dtree_res_pre.in_nte_count + 0.00001)], 'Dtree')

            # deleting tree edges
            #update_average_runtime(testcase, "deletion_te", [current_time,
            #                        Dtree_res.de_te_time / (Dtree_res.de_te_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "deletion_te",
                                   [current_time, (Dtree_res.de_te_time - Dtree_res_pre.de_te_time) /
                                    (Dtree_res.de_te_count - Dtree_res_pre.de_te_count + 0.00001)], 'Dtree')

            # deleting non-tree edges
            #update_average_runtime(testcase, "deletion_nte", [current_time,
            #                        Dtree_res.de_nte_time / (Dtree_res.de_nte_count + 0.00001)], 'Dtree')
            update_average_runtime(testcase,
                                   "deletion_nte",
                                   [current_time, (Dtree_res.de_nte_time - Dtree_res_pre.de_nte_time) /
                                    (Dtree_res.de_nte_count - Dtree_res_pre.de_nte_count + 0.00001)], 'Dtree')
            copyRes(Dtree_res, Dtree_res_pre)
            # output distributions of average distances between nodes and roots
            # count = len(test_points) # number of snapshots
            count_snapshot += 1  # number of snapshots
            #output_average_dist(distance_data, count, testcase, isSmallGraph)
            output_average_dist_by_method(Dtree_accumulated_dist, count_snapshot, testcase, 'Dtree')

    print("# of total updates: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count +
                                 Dtree_res.de_nte_count + Dtree_res.de_te_count))
    print("# of insertions: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count))
    print("# of deletions: %d." %(Dtree_res.de_nte_count + Dtree_res.de_te_count))



