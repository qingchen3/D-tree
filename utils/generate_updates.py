import sys
from _collections import defaultdict
from Class.Res import Res
from utils.IO import setup
from os.path import join, isfile
from os import listdir
from utils.tree_utils import order
import random
from timeit import default_timer as timer
import shutil


if __name__ == '__main__':
    sys.setrecursionlimit(50000000)
    testcase = sys.argv[1]
    # if testcase != 'scholar':
    #    raise ValueError("filename has to be scholar.")

    # setup starting point and ending point
    start_timestamp = 1800
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

    data_folder = './temp/'
    data_filenames = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
    current_time = start_timestamp
    # while current_time <= end_timestamp + survival_time:

    insertion_count = 0  # the number of insertions
    deletion_count = 0  # the number of deletions

    while current_time <= end_timestamp:
        # loop records and start with the record with current_time
        run_time = timer()

        temp_insertion_count = 0  # the number of insertions
        temp_deletion_count = 0  # the number of insertions
        if current_time <= end_timestamp:
            if str(current_time) in data_filenames:
                with open(join(data_folder, str(current_time)), 'r') as reader:
                    writer = open('res/updates/%s/%d_insertion' % (testcase, current_time), 'w')
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
                        insertion_count += 1
                        temp_insertion_count += 1
                        writer.write("%d %d\n" % (a, b)) # write updates in disks
                    writer.flush()
                    writer.close()

        if current_time in expiredDict:
            writer = open('res/updates/%s/%d_deletion' % (testcase, current_time), 'w')
            for (a, b) in expiredDict[current_time]:
                del inserted_edge[(a, b)]
                writer.write("%d %d\n" % (a, b))
                deletion_count += 1
                temp_deletion_count += 1

            writer.flush()
            writer.close()

            del expiredDict[current_time]

        if current_time in test_points:

            print("In year %d," % current_time, "Run time: %f seconds." %(timer() - run_time),
                  "Generating %d insertions and %d deletions." %(temp_insertion_count, temp_deletion_count))
            print("In total %d insertions and %d deletions" %(insertion_count, deletion_count))
            print()

        current_time += 1
