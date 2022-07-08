import sys
from _collections import defaultdict
from utils import tree_utils
from utils.tree_utils import constructST_adjacency_list
from utils.graph_utils import loadGraph

from Dtree import Dtree_utils_split
from Dtree.DTNode import DTNode
from timeit import default_timer as timer

from Class.Res import Res
from utils.IO import setup
from utils.graph_utils import order


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

    _, Dtree = Dtree_utils_split.construct_BFS_tree(graph, 0, non_tree_edges)
    _, nDtree = Dtree_utils_split.construct_BFS_tree(graph, 0, non_tree_edges)

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

    merges = 0
    splits = 0

    nmerges = 0
    nsplits = 0

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


            # Dtree
            if a not in Dtree:
                Dtree[a] = DTNode(a)
            if b not in Dtree:
                Dtree[b] = DTNode(b)

            start = timer()
            root_a, distance_a = Dtree_utils_split.find_root(Dtree[a])
            root_b, distance_b = Dtree_utils_split.find_root(Dtree[b])
            go_to_root_Dtree = timer() - start

            if root_a.val != root_b.val:
                merges += 1
                edges_num += 1
                Dtree_res.in_te_count += 1
                start = timer()
                Dtree_utils_split.insert_te(Dtree[a], Dtree[b], root_a, root_b)
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
                    Dtree_utils_split.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
                    Dtree_res.in_nte_time += (timer() - start + go_to_root_Dtree)


            # nDtree, navie Dtree
            if a not in nDtree:
                nDtree[a] = DTNode(a)
            if b not in nDtree:
                nDtree[b] = DTNode(b)

            start = timer()
            root_a, distance_a = Dtree_utils_split.find_root(nDtree[a])
            root_b, distance_b = Dtree_utils_split.find_root(nDtree[b])
            go_to_root_nDtree = timer() - start

            if root_a.val != root_b.val:
                nmerges += 1
                nDtree_res.in_te_count += 1
                start = timer()
                Dtree_utils_split.insert_te_simple(nDtree[a], nDtree[b], root_a, root_b)
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
                    Dtree_utils_split.insert_nte_simple(nDtree[a], nDtree[b])
                    nDtree_res.in_nte_time += (timer() - start + go_to_root_nDtree)

        if current_time in expiredDict:

            for (a, b) in expiredDict[current_time]:
                del inserted_edge[(a, b)]
                edges_num -= 1
                # HK
                # Dtree
                if Dtree[a] in Dtree[b].nte or Dtree[b] in Dtree[a].nte:
                    Dtree_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils_split.delete_nte(Dtree[a], Dtree[b])
                    Dtree_res.de_nte_time += (timer() - start)
                else:
                    Dtree_res.de_te_count += 1
                    start = timer()
                    _, _, ss = Dtree_utils_split.delete_te(Dtree[a], Dtree[b])
                    Dtree_res.de_te_time += (timer() - start)
                    splits += ss

                # remove isolated nodes from v_set.
                if Dtree[a].parent is None and Dtree[a].size == 1:
                    v_set.remove(a)

                if Dtree[b].parent is None and Dtree[b].size == 1:
                    v_set.remove(b)

                # nDtree, naive Dtree
                if nDtree[a] in nDtree[b].nte or nDtree[b] in nDtree[a].nte:
                    nDtree_res.de_nte_count += 1
                    start = timer()
                    Dtree_utils_split.delete_nte(nDtree[a], nDtree[b])
                    nDtree_res.de_nte_time += (timer() - start)
                else:
                    nDtree_res.de_te_count += 1
                    start = timer()
                    _, _, nss = Dtree_utils_split.delete_te_simple(nDtree[a], nDtree[b])
                    nDtree_res.de_te_time += (timer() - start)
                    nsplits += nss
                assert nsplits == splits
            del expiredDict[current_time]
        current_time += 1
        if current_time in test_points:
            # output to terminal
            print("timestamp:%d" % current_time)
            print("# of insertions: %d." % (Dtree_res.in_nte_count + Dtree_res.in_te_count))
            print("# of tree edges, merging two components: %d" % merges)
            print("# of deletions: %d." % (Dtree_res.de_nte_count + Dtree_res.de_te_count))
            print("# splits of connected components: %d" % splits)
            print()

    print("# of total updates: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count +
                                 Dtree_res.de_nte_count + Dtree_res.de_te_count))
    print("# of insertions: %d." %(Dtree_res.in_nte_count + Dtree_res.in_te_count))
    print("# of deletions: %d." %(Dtree_res.de_nte_count + Dtree_res.de_te_count))





