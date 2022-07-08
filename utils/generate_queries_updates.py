import sys
from _collections import defaultdict
from Class.Res import Res
from utils.IO import setup
from os.path import join, isfile
from os import listdir
from utils.tree_utils import order
import random
from timeit import default_timer as timer
from pathlib import Path
from utils.tree_utils import constructST_adjacency_list, generatePairs
from Dtree import Dtree_utils
from Dtree.DTNode import DTNode
import os


if __name__ == '__main__':
    sys.setrecursionlimit(50000000)
    testcase = sys.argv[1]
    # if testcase != 'scholar':
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

    print(survival_time,
          "%d tests, first test: %d, last test: %d" % (len(test_points), test_points[0], test_points[-1]))
    print(start_timestamp, end_timestamp)
    print(test_points)

    # start from an empty graph
    idx = 0

    expiredDict = defaultdict(set)
    inserted_edge = defaultdict()

    # distribution of distance between root and nodes
    Dtree_dist_data = defaultdict(int)

    insertion_count = 0
    deletion_count = 0

    steps_DT_nte = 0

    v_set = set()

    data_folder = './input/scholar/insertions'
    data_filenames = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
    current_time = start_timestamp
    # while current_time <= end_timestamp + survival_time:

    count = 0  # the number of generated queries
    max_priority = sys.maxsize
    graph = defaultdict(set)
    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)

    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)

    while current_time <= end_timestamp + survival_time + 10: # 2019 + 5
        # loop records and start with the record with current_time
        run_time = timer()
        if current_time <= end_timestamp + survival_time + 10:
            insertions_file = join(data_folder, "%d" % current_time)
            if Path(insertions_file).exists():
                with open(join(data_folder, str(current_time)), 'r') as reader:
                    for line in reader.readlines():
                        items = line.rstrip().split()
                        a = int(items[0])
                        b = int(items[1])
                        if (a, b) not in inserted_edge:  # a new edge
                            inserted_edge[(a, b)] = current_time + survival_time  # we keep the expired time for the inserted edge.
                            expiredDict[current_time + survival_time].add((a, b))
                        else:  # re-insert this edge, refresh the expired timestamp
                            expired_ts = inserted_edge[(a, b)]
                            expiredDict[expired_ts].remove((a, b))
                            inserted_edge[(a, b)] = current_time + survival_time  # we refresh the expired time for the inserted edge.
                            expiredDict[current_time + survival_time].add((a, b))

                        if a not in v_set:
                            v_set.add(a)
                        if b not in v_set:
                            v_set.add(b)

                        # Dtree
                        if a not in Dtree:
                            Dtree[a] = DTNode(a)
                        if b not in Dtree:
                            Dtree[b] = DTNode(b)

                        root_a, distance_a = Dtree_utils.find_root(Dtree[a])
                        root_b, distance_b = Dtree_utils.find_root(Dtree[b])

                        if root_a.val != root_b.val:
                            Dtree_utils.insert_te(Dtree[a], Dtree[b], root_a, root_b)
                        else:  # a and b are connected
                            if Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]:
                                continue
                            # count running time for inserting a non tree edge in DT
                            Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)

        if current_time in expiredDict:
            p = "./input/%s/deletion" % testcase
            if not os.path.exists(p):
                os.makedirs(p, exist_ok = True)

            writer = open('./input/%s/deletions/%d' % (testcase, current_time), 'w')
            for (a, b) in expiredDict[current_time]:
                del inserted_edge[(a, b)]
                writer.write("%d %d\n" % (a, b))
                # Dtree
                if Dtree[a] in Dtree[b].nte or Dtree[b] in Dtree[a].nte:
                    Dtree_utils.delete_nte(Dtree[a], Dtree[b])
                else:
                    Dtree_utils.delete_te(Dtree[a], Dtree[b])

            writer.flush()
            writer.close()

            del expiredDict[current_time]

        # generating queries
        if current_time in test_points:
            # output to terminal
            # generating queries is expensive!!
            # if there are more than 1 million vertices, we update generated 50 million queires every 10 test points.
            #    since the graphs are quite stable and generating 50 million queries per test points are expensive.
            # else, we generate queries every two test points
            p = "./input/%s/queries" % testcase
            if not os.path.exists(p):
                os.makedirs(p, exist_ok = True)

            tt = timer()  # time measurement for generating queries.
            v_list = list(v_set)
            V = len(v_set)
            print("current_time: %d, %d vertices." %(current_time, V), " --> generating queires")
            c = 50000000
            writer = open('./input/%s/queries/%d' % (testcase, current_time), 'w')
            count = 0
            pairs = generatePairs(v_set)
            for u, v in pairs:
                count += 1
                writer.write("%d %d\n" % (u, v))
            writer.flush()
            writer.close()

            tt_time = timer() - tt

            # output vertices
            p = "./input/%s/vertices" % testcase
            if not os.path.exists(p):
                os.makedirs(p, exist_ok = True)
            writer = open('./input/%s/vertices/%d' % (testcase, current_time), 'w')
            for u in v_set:
                writer.write("%d\n" %u)
            writer.flush()
            writer.close()
            print("In year %d," % current_time, ' %d vertices in graph.' % len(v_set),
                  "Total run time: %f seconds." %(timer() - run_time),
                  "Generating %d queries used %f seconds." %(count, tt_time))
            print()

        current_time += 1
