from _collections import defaultdict
from queue import PriorityQueue
from timeit import default_timer as timer
from utils.graph_utils import loadGraph
import sys
from Dtree.DTNode import DTNode
from Dtree import Dtree_utils
from utils.tree_utils import constructST_adjacency_list
from utils.tree_utils import generatePairs
import queue


def load_example():
    # example graph in DASFAA paper

    Suc = defaultdict(set)
    Pre = defaultdict(set)

    Suc[1].add(4)
    Pre[4].add(1)

    Suc[4].add(8)
    Pre[8].add(4)

    Suc[5].add(8)
    Pre[8].add(5)

    Suc[8].add(10)
    Pre[10].add(8)

    Suc[2].add(5)
    Pre[5].add(2)

    Suc[2].add(6)
    Pre[6].add(2)

    Suc[5].add(6)
    Pre[6].add(5)

    Suc[9].add(5)
    Pre[5].add(9)

    Suc[6].add(9)
    Pre[9].add(6)

    Suc[9].add(11)
    Pre[11].add(9)

    Suc[7].add(11)
    Pre[11].add(7)

    Suc[3].add(7)
    Pre[7].add(3)

    return Suc, Pre


# BFS on adjacency list
def BFS_adj(graph, u, v):
    if u == v:
        return True

    visited = set()
    q = queue.Queue()
    q.put(u)
    while q.qsize() > 0:
        x = q.get()
        if x == v:
            return True
        for i in graph[x]:
            if i not in visited:
                q.put(i)
                visited.add(i)

    return False


def DFS_adj(graph, u, v, visited):
    if u == v:
        return True

    visited.add(u)

    for i in graph[u]:
        if i not in visited:
            if i == v:
                return True

            if DFS_adj(graph, i, v, visited):
                return True

    return False


def topk(Suc, Pre, k):
    pq = PriorityQueue(k)
    for u in Suc.keys():
        Mu = len(Suc[u]) * len(Pre[u])
        if pq.qsize() < pq.maxsize:
            pq.put([Mu, u])
        else:
            top = pq.queue[0]
            if Mu > top[0]:
                pq.get()
                pq.put([Mu, u])
    D = []
    for [_, u] in pq.queue:
        D.append(u)
    return D


if __name__ == "__main__":
    sys.setrecursionlimit(50000000)

    graph = defaultdict(set)
    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)
    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)
    k = 64
    topK = []

    Suc = defaultdict(set)
    Pre = defaultdict(set)
    BL_in = dict()
    BL_out = dict()
    DL_in = defaultdict(set)
    DL_out = defaultdict(set)

    folder = 'dataset/'
    testcase = sys.argv[1]
    records = loadGraph(testcase)
    start = timer()

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
    print("inserting edges in DTree uses %f" %(timer() - start))

    v_sets = set()
    G_adj = defaultdict(set)
    for a, b, _ in records:
        v_sets.add(a)
        v_sets.add(b)
        G_adj[a].add(b)
        G_adj[b].add(a)


    v_list = list(v_sets)
    test_edges = generatePairs(v_list)
    print("%d all pairs of nodes are generated." %(len(test_edges)))


    start = timer()
    for (x, y) in test_edges:
        Dtree_utils.query_simple(Dtree[x], Dtree[y])
    print("querying in DTree takes", timer() - start)

    print("Test on DFS")
    c = 0
    start = timer()
    for (x, y) in test_edges:
        DFS_adj(G_adj, x, y, set())
        c += 1
        if c % 10000 == 0:
            print("Runnning %d queries takes %f seconds" %(c, timer() - start))
    print("querying using DFS takes", timer() - start)

    print("Test on BFS")
    c = 0
    start = timer()
    for (x, y) in test_edges:
        BFS_adj(G_adj, x, y)
        c += 1
        if c % 10000 == 0:
            print("Runnning %d queries takes %f seconds" %(c, timer() - start))
    print("querying using BFS takes", timer() - start)



