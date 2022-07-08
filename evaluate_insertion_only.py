from InsertionOnly import UnionFind
from _collections import defaultdict
from timeit import default_timer as timer
from utils.graph_utils import loadGraph
import sys
import numpy as np
from utils.tree_utils import generatePairs
from utils.tree_utils import constructST_adjacency_list
from Dtree import Dtree_utils
from Dtree.DTNode import DTNode
from BitVector import BitVector
from InsertionOnly.DBL import compute_topK_leaves, DL_batch_construct, BL_batch_construct, query, hash
from pathlib import Path
from tempfile import NamedTemporaryFile
import csv
import shutil


def write_result(testcase, result_type, data, method):
    if result_type == 'update':
        filename = 'res/insertiononly_update.csv'
    elif result_type == 'query':
        filename = 'res/insertiononly_query.csv'
    else:
        raise ValueError("invalid result type.")

    if testcase not in ['wiki', 'messages', 'dnc', 'call', 'fb',
                        'tech', 'enron', 'stackoverflow', 'youtube', 'dblp',  'scholar']:
        raise ValueError(" testcase not in ['wiki', 'messages', 'dnc', 'call', 'fb', "
                         "'tech', 'enron', 'stackoverflow', 'youtube', 'dblp',  'scholar']")

    if method not in ['UnionFind', 'Dtree', 'DBL']:
        raise ValueError("method not in ['UnionFind', 'Dtree', 'DBL']")

    labels = {'wiki': 'WI', 'messages': 'MS', 'dnc': 'DNC', 'call': 'CA', 'fb': 'FB',
             'tech': 'Tech', 'enron': 'EN', 'stackoverflow': 'ST', 'youtube': 'YT', 'scholar': 'SC'}

    testcase_ = labels[testcase]

    method_index = {'UnionFind': 1, 'Dtree': 2, 'DBL': 3}
    idx = method_index[method]
    if not Path(filename).exists():
        writer = open(filename, 'w')
        writer.write('Graph,UnionFind,DTree,DBL\n')
        writer.write("Tech,0,0,0\n"
                     "EN,0,0,0\nST,0,0,0\n"
                     "YT,0,0,0\nSC,0,0,0\n"
                     )
        writer.flush()
        writer.close()

    tempfile = NamedTemporaryFile('w+t', newline = '', delete = False)
    with open(filename, 'r', newline = '') as csvFile, tempfile:
        reader = csv.reader(csvFile, delimiter = ',', quotechar = '"')
        writer = csv.writer(tempfile, delimiter = ',', quotechar = '"')
        for row in reader:
            case = row[0]
            if case != testcase_:
                writer.writerow(row)
            else:
                items = []
                for k in range(len(row)):
                    items.append(row[k])
                t, c = data
                items[idx] = t / (c + 0.00001)
                writer.writerow(items)
    shutil.move(tempfile.name, filename)


if __name__ == '__main__':
    folder = 'dataset/'
    testcase = sys.argv[1]
    records = loadGraph(testcase)

    v_sets = set()
    G_adj = defaultdict(set)

    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(G_adj, 0)
    _, Dtree = Dtree_utils.construct_BFS_tree(G_adj, 0, non_tree_edges)

    start = timer()
    for a, b, _ in records:
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
            # (a, b) is a new  non tree edge
            if not (Dtree[a].parent == Dtree[b] or Dtree[b].parent == Dtree[a]) and \
                    not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[a].nte):
                Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)
    update_Dtree = timer() - start
    print("inserting edges in DTree uses %f" %update_Dtree)

    r = np.zeros(100000000, dtype = int)
    p = np.zeros(100000000, dtype = int)

    start = timer()
    for a, b, _ in records:
        if p[a] == 0:
            p[a] = a
        if p[b] == 0:
            p[b] = b
        if UnionFind.query(p, a, b):
            UnionFind.union(r, p, a, b)
    update_UnionFind = timer() - start
    print("inserting edges in Union Find uses %f" %update_UnionFind)

    k = 64
    bit_k = 64  # k' in the paper
    topK = []
    leaf_nodes = set()
    Suc = defaultdict(set)
    Pre = defaultdict(set)
    BL_in = dict()
    BL_out = dict()
    start = timer()
    for a, b, _ in records:
        # an undirected edge a-b is treated as a->b and b->a
        # add a->b
        Suc[a].add(b)
        Pre[b].add(a)

        # add b->a
        Suc[b].add(a)
        Pre[a].add(b)

        if a not in BL_out:  # a not in BL_in
            pos = hash(a, bit_k)
            BL_out[a] = BitVector(size = bit_k)
            BL_out[a][pos] = 1

            BL_in[a] = BitVector(size = bit_k)
            BL_in[a][pos] = 1
        if b not in BL_out:  # b not in BL_out
            pos = hash(b, bit_k)
            BL_out[b] = BitVector(size = bit_k)
            BL_out[b][pos] = 1

            BL_in[b] = BitVector(size = bit_k)
            BL_in[b][pos] = 1
    topK, leaves = compute_topK_leaves(Suc, Pre, k)
    DL_in, DL_out = DL_batch_construct(Suc, Pre, topK)
    BL_batch_construct(Suc, Pre, leaves, BL_in, BL_out, bit_k)
    update_DBL = timer() - start
    print("inserting edges in DBL takes %f seconds." % update_DBL)

    write_result(testcase, 'update', [update_UnionFind, len(records)], 'UnionFind')
    write_result(testcase, 'update', [update_Dtree, len(records)], 'Dtree')
    write_result(testcase, 'update', [update_DBL, len(records)], 'DBL')

    for a, b, _ in records:
        v_sets.add(a)
        v_sets.add(b)
        #G_adj[a].add(b)
        #G_adj[b].add(a)

    v_list = list(v_sets)
    test_edges = generatePairs(v_list)
    print("%d all pairs of nodes are generated." %(len(test_edges)))

    start = timer()
    for (x, y) in test_edges:
        Dtree_utils.query_simple(Dtree[x], Dtree[y])
    query_Dtree = timer() - start
    print("querying in DTree takes", query_Dtree, 'seconds')
    print()

    start = timer()
    for (x, y) in test_edges:
        query(Suc, DL_in, DL_out, BL_in, BL_out, x, y, verbose = False)
    query_DBL = timer() - start
    print("querying in DBL takes", query_DBL, 'seconds')

    start = timer()
    for (x, y) in test_edges:
        # assert UnionFind.query(p, x, y) == Dtree_utils.query_simple(Dtree[x], Dtree[y])
        UnionFind.query(p, x, y)
    query_UnionFind = timer() - start
    print("querying in Union find takes", query_UnionFind, 'seconds')
    print()
    write_result(testcase, 'query', [query_UnionFind, len(test_edges)], 'UnionFind')
    write_result(testcase, 'query', [query_Dtree, len(test_edges)], 'Dtree')
    write_result(testcase, 'query', [query_DBL, len(test_edges)], 'DBL')
