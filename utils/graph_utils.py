from _collections import defaultdict
import queue
import lxml.etree as ET
import os
import time, datetime
import sys


def loadGraph(testcase):
    edges = []
    if testcase == "osmswitzerland":
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split()
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, 1])
    elif testcase == 'TX':
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split('\t')
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, 1])

    elif testcase == "stackoverflow":
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split()
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, int(items[2])])
        edges.sort(key = lambda x: x[2])
    elif testcase == 'dnc':
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split(',')
            if items[0] == items[1]:
                continue
            t = int(items[2])
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, t])
        edges.sort(key = lambda x: x[2])
    elif testcase == 'enron':
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines[1:]:
            items = line.rstrip().split()
            if items[0] == items[1]:
                continue
            t = int(items[3])
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, t])
        edges.sort(key = lambda x: x[2])
    elif testcase == 'youtube':
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split('\t')
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, int(time.mktime(datetime.datetime.strptime(items[2], "%Y-%m-%d").timetuple()))])
        edges.sort(key = lambda x: x[2])
    elif testcase == 'tech':
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            if line.startswith('%'):
                continue
            items = line.rstrip().split()
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, int(items[3])])
        edges.sort(key = lambda x: x[2])

    elif testcase == 'wiki':
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split(" ")
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, int(items[3])])
        edges.sort(key = lambda x: x[2])
    elif testcase in ['fb', 'messages', 'call']:
        lines = open("datasets/" + testcase, 'r').readlines()
        for line in lines:
            items = line.rstrip().split(',')
            if items[0] == items[1]:
                continue
            u, v = order(int(items[0]), int(items[1]))
            edges.append([u, v, int(float(items[2]))])
        edges.sort(key = lambda x: x[2])
    elif testcase == 'dblp':
        # place the dtd_file "dblp.dtd" with "dblp" data file
        data_dir = 'datasets'
        data_file = 'dblp'
        name2id = dict()
        idx = 0
        for event, element in ET.iterparse(os.path.join(data_dir, data_file), dtd_validation = True):
            # print all children
            coauthors = set()
            for child in element:
                if child.tag == 'author':
                    coauthors.add(child.text)
                if child.tag == 'year':
                    year = int(child.text)
            coauthors = list(coauthors)
            if len(coauthors) > 1:
                for name in coauthors:
                    if name not in name2id:
                        name2id[name] = idx
                        idx += 1

                for ii in range(0, len(coauthors)):
                    for jj in range(ii + 1, len(coauthors)):
                        a = name2id[coauthors[ii]]
                        b = name2id[coauthors[jj]]
                        if a == b:
                            continue
                        (u, v) = order(a, b)
                        edges.append([u, v, year])
        edges.sort(key = lambda x: x[2])
    #elif testcase == 'scholar':
    #    lines = open("datasets/" + testcase, 'r').readlines()
    #    for line in lines:
    #        items = line.rstrip().split(' ')
    #        edges.append([items[0], items[1], int(items[2])])
    #    edges.sort(key = lambda x: x[2])
    elif testcase == 'test1':
        edges = [(1, 2, 0), (1, 3, 0), (1, 4, 0), (2, 3, 0), (3, 4, 0), (2, 5, 0), (3, 5, 0), (4, 5, 0)]

    return edges


def constructST_adjacency_list(graph, n):
    #compute spanning tree
    st = defaultdict(set)
    visited = [False] * (n + 1)
    for u in range(1, n):
        if not visited[u]:
            visited[u] = True
            q = queue.Queue()
            if len(graph[u]) == 0:
                visited[u] = True
                continue
            q.put(u)
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
                q = new_q
    return st


# BFS on adjacency maxtrix
def BFS(graph, u, v):
    if u == v:
        return True

    N = len(graph)
    visited = [False] * len(graph)
    q = queue.Queue()
    q.put(u)
    visited[u] = True
    while q.qsize() > 0:
        new_q = queue.Queue()
        while q.qsize() > 0:
            x = q.get()
            if x == v:
                return True
            for i in range(1, N):
                if graph[x][i] != 0 and not visited[i]:
                    new_q.put(i)
                    visited[i] = True

        q = new_q

    return False


# BFS on adjacency list
def BFS_adj(graph, n, u, v):
    if u == v:
        return True

    visited = [False] * (n + 1)
    q = queue.Queue()
    q.put(u)
    visited[u] = True
    while q.qsize() > 0:
        new_q = queue.Queue()
        while q.qsize() > 0:
            x = q.get()
            if x == v:
                return True
            for i in graph[x]:
                if not visited[i]:
                    new_q.put(i)
                    visited[i] = True

        q = new_q

    return False


# compute the best BFS with minimum S_d
def best_BFS(graph, n, r):
    #BFS trees for one connected component

    # BFS to find all vertices
    vertices_set = set()  # vertices in one connected component
    visited = [False] * (n + 1)
    q = queue.Queue()
    q.put(r)
    visited[r] = True
    while q.qsize() > 0:
        x = q.get()
        vertices_set.add(x)
        for i in graph[x]:
            if not visited[i]:
                q.put(i)
                visited[i] = True

    minimum_dist = sys.maxsize
    target = None

    for u in vertices_set:
        distances = 0
        visited = [False] * (n + 1)
        q = queue.Queue()
        q.put(u)
        visited[u] = True
        level = 1
        while q.qsize() > 0:
            new_q = queue.Queue()
            while q.qsize() > 0:
                x = q.get()
                for i in graph[x]:
                    if not visited[i]:
                        new_q.put(i)
                        visited[i] = True
                        #st[x].add(i)
                        #st[i].add(x)
                        distances += level
            level += 1
            q = new_q
        if distances < minimum_dist:
            minimum_dist = distances
            #bfs_tree = st.copy()
            target = u
    return target


def order(a, b):
    if a < b:
        return a, b
    else:
        return b, a
