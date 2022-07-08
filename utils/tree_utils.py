import queue
from _collections import defaultdict
import random


def order(a, b):

    if a < b:
        return a, b
    else:
        return b, a


def find_root_with_steps(node):
    p = node
    steps = 0
    while p.parent is not None:
        p = p.parent
        steps += 1
    return p, steps


def find_root(node):
    p = node

    while p.parent is not None:
        p = p.parent
    return p


def generatePairs(v_set):
    v_list = list(v_set)
    V = len(v_list)
    c = 50000000  # 50 millions, 5 millions for duplicate pairs
    pairs = set()
    if c > (V * (V - 1)) // 2:  # generate queries for all pairs of vertices if the number is smaller than 50 million.
        for i in range(V):
            for j in range(i + 1, V):
                pairs.add((v_list[i], v_list[j]))
    elif 5 * c > (V * (V - 1)) // 2 >= c:
        temp = []
        for i in range(V):
            for j in range(i + 1, V):
                temp.append((v_list[i], v_list[j]))
        pairs = set(random.sample(temp, c))
    elif V < 1000000:
        while len(pairs) < c:
            [u, v] = random.sample(v_list, 2)
            (u, v) = order(u, v)
            if (u, v) not in pairs:
                pairs.add((u, v))
    else:
        while len(pairs) < c:
            [u, v] = random.sample(v_list, 2)
            (u, v) = order(u, v)
            pairs.add((u, v))
    del v_list
    return pairs


def readQueries(testcase, test_point):
    reader = open('queries/%s/%d' %(testcase, test_point))
    queries = set()
    for line in reader.readlines():
        u, v = line.rstrip().split()
        u = int(u)
        v = int(v)
        queries.add((u, v))
    return queries


def query(u, v, active_occurrence_dict):
    if u == v:
        return True

    if u not in active_occurrence_dict or v not in active_occurrence_dict:
        return False
    root_u = find_root(active_occurrence_dict[u])
    root_v = find_root(active_occurrence_dict[v])
    if root_u != root_v:
        return False
    else:
        return True


def toRoot(node):
    dist = 0
    while node.parent is not None:
        node = node.parent
        dist += 1
    return dist


def constructST_adjacency_list(graph, n):
    tree_edges = set()
    non_tree_edges = set()
    st = defaultdict(set)
    visited = [False] * (n + 1)

    for u in range(1, n):
        if not visited[u]:
            visited[u] = True
            q = queue.Queue()
            q.put(u)
            visited[u] = True
            while q.qsize() > 0:
                new_q = queue.Queue()
                while q.qsize() > 0:
                    x = q.get()
                    for y in graph[x]:
                        if not visited[y]:
                            st[x].add(y)
                            st[y].add(x)
                            new_q.put(y)
                            visited[y] = True
                            (a, b) = order(x, y)
                            if (a, b) not in tree_edges: #add tree edge (x, y) where x < y
                                tree_edges.add((a, b))
                q = new_q

    #find non-tree edges
    for u, adj_vertices in graph.items():
        for v in adj_vertices:
            a = u
            b = v
            (a, b) = order(a, b)
            if (a, b) not in tree_edges:
                non_tree_edges.add((a, b))

    return st, tree_edges, non_tree_edges


def obtainETRs(st, n):

    visited = [False] * (n + 1)
    etrs = []
    for i in range(1, n):
        if i not in st or visited[i]:
            continue
        etrs.append(DFS(st, i, visited))
    return etrs


def DFS_stack(sf, v, visited):
    etr = []
    s = []
    s.append(v)
    etr.append(v)
    visited[v] = True
    while len(s) > 0:
        for x in sf[v]:
            if not visited[x]:
                visited[x] = True
                etr.append(x)
                break


def DFS(sf, v, visited):

    visited[v] = True
    etr = []
    etr.append(v)
    if len(sf[v]) > 0:
        for x in sf[v]:
            if not visited[x]:
                visited[x] = True
                etr.extend(DFS(sf, x, visited))
                etr.append(v)
    return etr


def obtainETR(st, v):

    etr = []
    etr.append(v)
    if len(st[v]) > 0:
        for x in st[v]:
            st[x].remove(v)
            etr.extend(obtainETR(st, x))
            etr.append(v)

    return etr


def coding(pointer):
    code = ''
    while pointer.parent is not None:
        p = pointer.parent
        if pointer == p.left:
            code = '0' + code
        else:
            code = '1' + code
        pointer = p

    return code


def smaller(str1, str2):
    L = min(len(str1), len(str2))
    i = 0
    while i < L:
        # print(str1[i], str2[i])
        if str1[i] < str2[i]:
            return True
        elif str1[i] > str2[i]:
            return False
        i += 1

    if len(str1) < len(str2):
        return str2[i] == '1'
    else:
        return str1[i] == '0'


def sort(tree_edges_pointer):
    maximum = 0
    minimum = 0
    codes = []
    for pointer in tree_edges_pointer:
        codes.append(coding(pointer))
    for i in range(1, len(tree_edges_pointer)):

        if smaller(codes[maximum], codes[i]):
            maximum = i
        if smaller(codes[i], codes[minimum]):
            minimum = i

    return tree_edges_pointer[minimum], tree_edges_pointer[maximum]

