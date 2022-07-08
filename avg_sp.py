from Dtree import Dtree_utils
from HK import HK_utils
import sys
from collections import defaultdict
from utils.tree_utils import constructST_adjacency_list
from Class.Res import Res
from timeit import default_timer as timer
from HK.HKNode import HKNode
import HK.updates as HKupdate
from Dtree.DTNode import DTNode
from utils.tree_utils import generatePairs
from utils import tree_utils
import random
import queue


def BFS_adj(graph, n, u, v):
    if u == v:
        return True

    visited = [False] * (n + 1)
    q = queue.Queue()
    q.put(u)
    visited[u] = True
    dist = 0
    while q.qsize() > 0:
        new_q = queue.Queue()
        while q.qsize() > 0:
            x = q.get()
            if x == v:
                return dist
            for i in graph[x]:
                if not visited[i]:
                    new_q.put(i)
                    visited[i] = True

        q = new_q
        dist += 1

    return -1


def averageAllPairsDist(edges, N):
    graph = defaultdict(set)
    v_list = [i for i in range(0, N + 1)]
    for (u, v) in edges:
        graph[u].add(v)
        graph[v].add(u)
    count = 0
    sum_dist = 0
    for i in range(0, len(v_list)):
        for j in range(i + 1,  len(v_list)):
            d = BFS_adj(graph, N, v_list[i], v_list[j])
            count += 1
            if d < 0:
                print(v_list[i], v_list[j], d)
                raise ValueError("distance is negative")
            sum_dist += d

    return sum_dist / count


def generateGraph(N):
    # we generate graph with b branches in which contain the same number of nodes
    graphs = defaultdict(list)
    parameters = [24, 30, 40, 80, 100, 120, 160, 240, 480]
    for b in parameters:
        branches = [0] * b
        for i in range(1, N, b):
            for x in range(b):
                if i + x > N:
                    break
                graphs[b].append((branches[x], i + x))
                branches[x] = i + x

    return parameters, graphs


if __name__ == '__main__':
    max_priority = sys.maxsize
    graph = defaultdict(set)
    N = 480
    parameters, graphs = generateGraph(N)

    spanningtree, tree_edges, non_tree_edges = constructST_adjacency_list(graph, 0)

    _, Dtree = Dtree_utils.construct_BFS_tree(graph, 0, non_tree_edges)

    HK_forest, HK_tree_edges, HK_non_tree_edges, HK_active_occurrence_dict, HK_tree_edges_pointers = \
        HK_utils.HK_constructSF(graph, 0, max_priority)

    HK_res = Res()
    Dtree_res = Res()
    v_set = set()
    writer = open("res/avg_sp.dat", "w")
    writer.write("avg_sp HK Dtree\n")

    for k in parameters:
        for (a, b) in graphs[k]:
            # HK

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

            root_a, distance_a = tree_utils.find_root_with_steps(HK_active_occurrence_dict[a])
            root_b, distance_b = tree_utils.find_root_with_steps(HK_active_occurrence_dict[b])

            v_set.add(a)
            v_set.add(b)

            if root_a.val != root_b.val:
                HKupdate.insert_tree_edge(a, root_a, b, root_b, HK_tree_edges, HK_active_occurrence_dict,
                                               HK_tree_edges_pointers, max_priority)

            else:  # a and b are connected
                if (a, b) not in HK_tree_edges and (a, b) not in HK_non_tree_edges:  # (a, b) is a new  non tree edge
                    HKupdate.insert_nontree_edge(a, b, HK_active_occurrence_dict, HK_non_tree_edges)

            # Dtree, Dtree with heuristics and balancing
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
                        not (Dtree[a] in Dtree[b].nte and Dtree[b] in Dtree[
                            a].nte):
                    # inserting a non tree edge
                    Dtree_utils.insert_nte(root_a, Dtree[a], distance_a, Dtree[b], distance_b)

        v_list = list(v_set)
        test_edges = generatePairs(v_list)

        start = timer()
        for (x, y) in test_edges:
            Dtree_utils.query(Dtree[x], Dtree[y])
        query_Dtree = timer() - start

        start = timer()
        for (x, y) in test_edges:
            tree_utils.query(x, y, HK_active_occurrence_dict)
        query_HK = timer() - start

        print(query_Dtree, query_HK)
        avg_sp = averageAllPairsDist(graphs[k], N)
        writer.write("%f %f %f\n" %(avg_sp, query_HK, query_Dtree))
        writer.flush()
    writer.close()