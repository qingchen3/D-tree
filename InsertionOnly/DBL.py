from _collections import defaultdict
import queue
from BitVector import BitVector
import heapq


def hash(x, k):
    x = ((x >> 16) ^ x) * 0x45d9f3b
    x = ((x >> 16) ^ x) * 0x45d9f3b
    x = (x >> 16) ^ x
    return x % k


def hash1(x, k):
    if x in [2, 3, 11]:
        return 1
    else:
        return 0


def is_leaf(Suc, Pre, x):
    return len(Suc[x]) * len(Pre[x]) == 1


def search_in_heap(key, heap):
    # time complexity of searching an element in a heap is O(n)
    # because w.l.o.g, in a min-heap, heap[i] <= heap[2 * i  + 1] and heap[i] <= heap[2 * i  + 2].
    # In other words, we need to traverse all elements in a heap for the searching of a specific element.
    max_len = len(heap)
    for i in range(max_len):
        if heap[i][1] == key:
            return i, heap[i][0]
    return -1, -1


def delete_in_heap(key, heap):
    max_len = len(heap)
    idx, _ = search_in_heap(key, heap)
    if idx == -1:
        return
    heap[idx] = heap[max_len - 1]
    del heap[max_len - 1]
    if idx == max_len - 1:
        return
    if heap[(idx - 1) >> 1][0] > heap[idx][0]:
        heapq._siftdown(heap, 0, idx)
    elif (2*idx + 1 < max_len - 1 and heap[idx][0] > heap[2*idx + 1][0]) or \
            (2* idx + 2 < max_len - 1 and heap[idx][0] > heap[2*idx + 2][0]):
        heapq._siftup(heap, idx)
    return


def DL_batch_update(Suc, Pre, DL_in, DL_out, topK):
    # Forward graph: Suc
    # Backward graph: Pre

    for _, S in topK:

        DL_in[S].add(S)
        DL_out[S].add(S)
        # Forward BFS
        Q = queue.Queue()
        Q.put(S)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if not DL_in[S].issubset(DL_in[x]):
                    Q.put(x)
                    DL_in[x].update(DL_in[S])

        # Backward BFS
        assert Q.empty()
        Q.put(S)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if not DL_out[S].issubset(DL_out[x]):
                    Q.put(x)
                    DL_out[x].update(DL_out[S])

    return DL_in, DL_out


def DL_batch_construct(Suc, Pre, D):
    # Forward graph: Suc
    # Backward graph: Pre

    DL_in = defaultdict(set)
    DL_out = defaultdict(set)
    for S in D:
        DL_in[S].add(S)
        DL_out[S].add(S)
        # Forward BFS
        Q = queue.Queue()
        Q.put(S)
        visited = set()
        visited.add(S)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                DL_in[x].add(S)
                if x not in visited:
                    Q.put(x)
                    visited.add(x)

        # Backward BFS
        assert Q.empty()
        Q.put(S)
        visited.clear()
        visited.add(S)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                DL_out[x].add(S)
                if x not in visited:
                    Q.put(x)
                    visited.add(x)

    return DL_in, DL_out


def DL_batch_construct(Suc, Pre, topK):
    # Forward graph: Suc
    # Backward graph: Pre

    DL_in = defaultdict(set)
    DL_out = defaultdict(set)
    for Mu, S in topK:
        DL_in[S].add(S)
        DL_out[S].add(S)
        # Forward BFS
        Q = queue.Queue()
        Q.put(S)
        visited = set()
        visited.add(S)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if x not in visited:
                    DL_in[x].add(S)
                    Q.put(x)
                    visited.add(x)

        # Backward BFS
        assert Q.empty()
        Q.put(S)
        visited.clear()
        visited.add(S)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if x not in visited:
                    DL_out[x].add(S)
                    Q.put(x)
                    visited.add(x)

    return DL_in, DL_out


def BL_batch_construct(Suc, Pre, leaves, BL_in, BL_out, bit_k):
    # Forward graph: Suc
    # Backward graph: Pre

    bit_leaves_map = defaultdict(set)
    for l in leaves:
        pos = hash(l, bit_k)
        bit_leaves_map[pos].add(l)

    for pos, vertices_set in bit_leaves_map.items():
        # Forward BFS
        Q = queue.Queue()
        visited = set()
        for v in vertices_set:
            Q.put(v)
            visited.add(v)

        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if x not in visited:
                    BL_in[x][pos] = 1
                    Q.put(x)
                    visited.add(x)

        # Backward BFS
        #Q_back = queue.Queue()
        #visited = set()
        #for v in vertices_set:
        #    Q_back.put(v)
        #    visited.add(v)

        #while not Q_back.empty():
        #    p = Q_back.get()
        #    for x in Pre[p]:
        #        if x not in visited:
        #            BL_out[x][pos] = 1
        #            Q_back.put(x)
        #            visited.add(x)
    return BL_in, BL_out


def batch_update_topK(Suc, Pre, s, topK, k):

    Mu = len(Suc[s]) * len(Pre[s])
    idx, mu = search_in_heap(s, topK)

    if len(topK) < k:
        if idx < 0:
            heapq.heappush(topK, (Mu, s))  # s becomes a landmark
            return
        elif idx > 0 and mu < Mu:
            delete_in_heap(s, topK)
            heapq.heappush(topK, (Mu, s))
            return
    else:
        if idx >= 0:  # s is already in the topK landmark
            if Mu > mu:
                delete_in_heap(s, topK)
                heapq.heappush(topK, (Mu, s))
        if idx == -1: # s is not in topK
            heapq.heapreplace(topK, (Mu, s))
    return


def compute_topK_leaves(Suc, Pre, k):
    topK = []
    leaves = []
    for v in Suc.keys():
        Mu = len(Suc[v]) * len(Pre[v])
        if Mu == 1:
            leaves.append(v)
        if len(topK) < k:
            heapq.heappush(topK, (Mu, v))
        elif Mu > topK[0][0]:
            heapq.heapreplace(topK, (Mu, v))
    return topK, leaves


def DL_insertion(DL_in, DL_out, Suc, Pre, u, v, topK, k):
    # insert a directed edge: u->v
    Suc[u].add(v)
    Pre[v].add(u)
    if u not in DL_in:
        DL_in[u] = set()
        DL_out[u] = set()
    if v not in DL_in:
        DL_in[v] = set()
        DL_out[v] = set()

    # update top K
    update_DL_and_topK(Suc, Pre, DL_in, DL_out, u, topK, k)
    update_DL_and_topK(Suc, Pre, DL_in, DL_out, v, topK, k)

    if len(DL_out[u] & DL_in[v]) == 0:
    #if not DL_in[u].issubset(DL_in[v]):

        # add DL_in[u] to DL_in [v]
        if not DL_in[u].issubset(DL_in[v]):
            DL_in[v].update(DL_in[u])
        # Forward BFS from v
        Q = queue.Queue()
        Q.put(v)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if not DL_in[u].issubset(DL_in[x]):
                    DL_in[x].update(DL_in[u])
                    Q.put(x)

        # add DL_out[v] to DL_out[u]
        if not DL_out[v].issubset(DL_out[u]):
            DL_out[u].update(DL_out[v])

        assert Q.empty()
        # Backward BFS from u
        Q.put(u)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if not DL_out[v].issubset(DL_out[x]):
                    DL_out[x].update(DL_out[v])
                    Q.put(x)
        if u == 7 and v == 30:
            print(u, DL_in[u], DL_out[u])
            print(v, DL_in[v], DL_out[v])
    return


def BL_batch_update(Suc, Pre, BL_in, BL_out, leaf_nodes, k):
    # Forward graph: Suc
    # Backward graph: Pre
    for u in leaf_nodes:
        if u not in BL_out:
            # BL_out[v].add(v)
            BL_out[u] = BitVector(size = k)
        BL_out[u][hash(u, k)] = 1

        # Backward BFS
        Q = queue.Queue()
        Q.put(u)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if x not in BL_out:
                    BL_out[x] = BitVector(size = k)
                if BitVector.count_bits(BL_out[u]) != BitVector.count_bits(BL_out[x] & BL_out[u]):
                    BL_out[x] = BL_out[x] | BL_out[u]
                    Q.put(x)

        # BL_in[v].add(v)
        if u not in BL_in:
            BL_in[u] = BitVector(size = k)
        BL_in[u][hash(u, k)] = 1

        # Forward BFS
        assert Q.empty()
        Q.put(u)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if x not in BL_in:
                    BL_in[x] = BitVector(size = k)
                if BitVector.count_bits(BL_in[u]) != BitVector.count_bits(BL_in[x] & BL_in[u]):
                    BL_in[x] = BL_in[x] | BL_in[u]
                    Q.put(x)

    return


def BL_batch(Suc, Pre):
    # Forward graph: Suc
    # Backward graph: Pre
    k = 2

    BL_in = dict()
    BL_out = dict()
    v_set = Suc.keys() | Pre.keys()

    for v in v_set:
        if len(Suc[v]) == 0:
            if v not in BL_out:
                # BL_out[v].add(v)
                BL_out[v] = BitVector(size = k)
            BL_out[v][hash(v, k)] = 1

            # Backward BFS
            Q = queue.Queue()
            Q.put(v)
            visited = set()
            visited.add(v)
            while not Q.empty():
                p = Q.get()
                for x in Pre[p]:
                    if x not in visited:
                        # BL_out[x].add(v)
                        if x not in BL_out:
                            BL_out[x] = BitVector(size = k)
                        BL_out[x][hash(v, k)] = 1

                        Q.put(x)
                        visited.add(x)

        if len(Pre[v]) == 0:
            # BL_in[v].add(v)
            if v not in BL_in:
                BL_in[v] = BitVector(size = k)
            BL_in[v][hash(v, k)] = 1

            # Forward BFS
            Q = queue.Queue()
            Q.put(v)
            visited = set()
            visited.add(v)
            while not Q.empty():
                p = Q.get()
                for x in Suc[p]:
                    if x not in visited:
                        # BL_in[x].add(v)
                        if x not in BL_in:
                            BL_in[x] = BitVector(size = k)
                        BL_in[x][hash(v, k)] = 1

                        Q.put(x)
                        visited.add(x)

    return BL_in, BL_out


def BL_insertion(BL_in, BL_out, Suc, Pre, u, v, k):
    # insert a directed edge: u->v

    if u not in BL_out or u not in BL_in:
        BL_out[u] = BitVector(size = k)
        BL_in[u] = BitVector(size = k)
        BL_in[u][hash(u, k)] = 1
    if v not in BL_out or v not in BL_in:
        BL_out[v] = BitVector(size = k)
        BL_in[v] = BitVector(size = k)
        BL_out[v][hash(v, k)] = 1

    if BitVector.count_bits(BL_out[u] & BL_in[v]) == 0:

        # Forward BFS
        Q = queue.Queue()
        Q.put(v)
        BL_in[v] = BL_in[v] | BL_in[u]
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if x not in BL_in:
                    BL_in[x] = BitVector(size = k)
                if BitVector.count_bits(BL_in[u]) != BitVector.count_bits(BL_in[u] & BL_in[x]):
                    BL_in[x] = BL_in[x] | BL_in[u]
                    Q.put(x)

        assert Q.empty()
        Q.put(u)
        BL_out[u] = BL_out[u] | BL_out[v]
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if x not in BL_out:
                    BL_out[x] = BitVector(size = k)
                if BitVector.count_bits(BL_out[v]) != BitVector.count_bits(BL_out[v] & BL_out[x]):
                    BL_out[x] = BL_out[x] | BL_out[v]
                    Q.put(x)
        return
    return


def DL_Intersec(DL_in, DL_out, x, y):
    return len(DL_out[x] & DL_in[y]) != 0


def BL_Contain(BL_in, BL_out, x, y):
    #print(x, y)
    #print("BL_in:", BitVector.count_bits(BL_in[x]), BitVector.count_bits(BL_in[x] & BL_in[y]))
    #print("BL_out:", BitVector.count_bits(BL_out[y]), BitVector.count_bits(BL_out[x] & BL_out[y]))
    return BitVector.count_bits(BL_in[x]) == BitVector.count_bits(BL_in[x] & BL_in[y])
    #return BitVector.count_bits(BL_in[x]) == BitVector.count_bits(BL_in[x] & BL_in[y]) \
    #       and BitVector.count_bits(BL_out[y]) == BitVector.count_bits(BL_out[x] & BL_out[y])


def query(Suc, DL_in, DL_out, BL_in, BL_out, u, v, verbose=False):
    if DL_Intersec(DL_in, DL_out, u, v):
        return True
    #if not BL_Contain(BL_in, BL_out, u, v) and not BL_Contain(BL_in, BL_out, v, u):
    if not BL_Contain(BL_in, BL_out, u, v):
        if verbose:
            print(BL_in[u], BL_out[u])
            print(BL_in[v], BL_out[v])
        return False
    if DL_Intersec(DL_in, DL_out, v, u):
        if verbose:
            raise ValueError("DL_Intersec(DL_in, DL_out, v, u)")
        return False
    if DL_Intersec(DL_in, DL_out, u, u) or DL_Intersec(DL_in, DL_out, v, v):  # u and v are landmarks
        if verbose:
            if DL_Intersec(DL_in, DL_out, u, u):
                print(v, DL_in[v], DL_out[v])
                print(u, DL_in[u], DL_out[u])
            if DL_Intersec(DL_in, DL_out, v, v):
                print(v, DL_in[v], DL_out[v])
                print(u, DL_in[u], DL_out[u])
            raise ValueError("DL_Intersec(DL_in, DL_out, u, u) or DL_Intersec(DL_in, DL_out, v, v)",
                             DL_Intersec(DL_in, DL_out, u, u), DL_Intersec(DL_in, DL_out, v, v))
        return False
    #print("RUN BFS")
    Q = queue.Queue()
    Q.put(u)
    visited = set()
    visited.add(u)
    while not Q.empty():
        w = Q.get()
        #print(w, Suc[w])
        for x in Suc[w]:
            if x == v:
                return True
            if DL_Intersec(DL_in, DL_out, u, x):
                #print(DL_in[u], DL_out[u])
                #print(DL_in[x], DL_out[x])
                continue
            if not BL_Contain(BL_in, BL_out, x, v) and not BL_Contain(BL_in, BL_out, v, x):
                #print(BL_Contain(BL_in, BL_out, x, v), BL_Contain(BL_in, BL_out, v, x))
                #print(BitVector.count_bits(BL_in[v]), BitVector.count_bits(BL_in[v] & BL_in[x]))
                #print(x, BL_in[x], BL_out[x])
                #print(v, BL_in[v], BL_out[v])
                continue
            if x not in visited:
                visited.add(x)
                Q.put(x)
    #print("end")
    return False


def BFS(Suc, u, v):

    # Forward BFS
    Q = queue.Queue()
    Q.put(u)
    visited = set()
    visited.add(u)
    while not Q.empty():
        p = Q.get()
        for x in Suc[p]:
            if x == v:
                return True
            if x not in visited:
                if x not in visited:
                    Q.put(x)
                    visited.add(x)

    return False


def BL_insertion_bak(BL_in, BL_out, Suc, Pre, u, v):
    # insert a directed edge: u->v
    #if len(Suc[u]) != 0 and len(Pre[v])!= 0:
    #    return

    # Forward BFS
    if BitVector.count_bits(BL_out[u] & BL_in[v]) == 0:
        Q = queue.Queue()
        Q.put(v)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if not BL_in[u].issubset(BL_in[x]):
                    BL_in[x] = BL_in[x] | BL_in[u]
                    Q.put(x)

        Q.clear()
        assert Q.empty()
        Q.put(u)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if not BL_out[v].issubset(BL_out[x]):
                    #BL_out[x].update(BL_out[v])
                    BL_out[x] = BL_out[x] | BL_out[v]
                    Q.put(x)


def DL_insertion_bak(DL_in, DL_out, Suc, Pre, u, v):
    # insert a directed edge: u->v

    if len(DL_out[u] & DL_in[v]) == 0:

        # Forward BFS
        if not DL_in[u].issubset(DL_in[v]):
            DL_in[v].update(DL_in[u])

        visited = set()
        Q = queue.Queue()
        Q.put(v)
        visited.add(v)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if not DL_in[u].issubset(DL_in[x]):
                    DL_in[x].update(DL_in[u])
                    if x not in visited:
                        Q.put(x)
                        visited.add(x)

        # Backward BFS
        if not DL_out[v].issubset(DL_out[u]):
            DL_out[u].update(DL_out[v])

        assert Q.empty()
        visited.clear()
        Q.put(u)
        visited.add(u)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if not DL_out[v].issubset(DL_out[x]):
                    DL_out[x].update(DL_out[v])
                    if x not in visited:
                        Q.put(x)
                        visited.add(x)
    return


def update_topK(item, topK, k):
    # topK is a list (a heap)
    Mu, s = item
    idx, mu = search_in_heap(s, topK)

    if len(topK) < k:
        if idx < 0:
            heapq.heappush(topK, (Mu, s))  # s becomes a landmark
        elif idx > 0 and mu < Mu:
            delete_in_heap(s, topK)
            heapq.heappush(topK, (Mu, s))
            return
    elif Mu < topK[0][0]:
        return
    else:
        if idx == -1:  # s is a new landmark without being in topK, add s to topK.
            # remove old landmark with least Mu in topK
            # add (Mu, s) to topK
            heapq.heapreplace(topK, (Mu, s))
        else:  # s is already in the topK landmark
            delete_in_heap(s, topK)
            heapq.heappush(topK, (Mu, s))
    return


def update_DL_and_topK(Suc, Pre, DL_in, DL_out, s, topK, k):
    # first, update topK landmarks
    # second, update DL if landmark nodes change.

    # topK is a list (a heap)
    Mu = len(Suc[s]) * len(Pre[s])
    idx, mu = search_in_heap(s, topK)

    if len(topK) < k:
        if idx < 0:
            heapq.heappush(topK, (Mu, s))  # s becomes a landmark
            DL_in[s].add(s)
            DL_out[s].add(s)
            '''
            Q = queue.Queue()
            Q.put(s)
            while not Q.empty():
                p = Q.get()
                for x in Suc[p]:
                    if s not in DL_in[x]:
                        DL_in[x].add(s)
                        Q.put(x)

            # Backward BFS to remove z from DL_out
            Q.put(s)
            while not Q.empty():
                p = Q.get()
                for x in Pre[p]:
                    if x not in DL_out[s]:
                        DL_out[x].add(s)
                        Q.put(x)
            '''
            return
        elif idx > 0 and mu < Mu:
            delete_in_heap(s, topK)
            heapq.heappush(topK, (Mu, s))
            return

    if Mu <= topK[0][0]:
        return

    if idx >= 0:  # s is already in the topK landmark
        delete_in_heap(s, topK)
        heapq.heappush(topK, (Mu, s))
    if idx == -1:  # s is a new landmark without being in topK, add s to topK.
        # remove old landmark with least Mu in topK

        z = topK[0][1]
        assert z != s
        assert z in DL_in[z] and z in DL_out[z]

        DL_in[z].remove(z)
        DL_out[z].remove(z)

        # Forward BFS to remove z from DL_in
        Q = queue.Queue()
        Q.put(z)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                if z in DL_in[x]:
                    DL_in[x].remove(z)
                    Q.put(x)

        # Backward BFS to remove z from DL_out
        Q.put(z)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                if z in DL_out[x]:
                    DL_out[x].remove(z)
                    Q.put(x)

        # add (Mu, s) to topK
        heapq.heapreplace(topK, (Mu, s))
        # add x as a new landmark
        DL_in[s].add(s)
        DL_out[s].add(s)
        '''
        Q.put(s)
        while not Q.empty():
            p = Q.get()
            for x in Suc[p]:
                # if s not in DL_in[x]:
                #    DL_in[x].add(s)
                if not DL_in[s].issubset(DL_in[x]):
                    DL_in[x].update(DL_in[s])
                    Q.put(x)

        # Backward BFS to remove z from DL_out
        Q.put(s)
        while not Q.empty():
            p = Q.get()
            for x in Pre[p]:
                # if x not in DL_out[s]:
                #    DL_out[x].add(s)
                if not DL_out[s].issubset(DL_out[x]):
                    DL_out[x].update(DL_out[s])
                    Q.put(x)

        assert z not in DL_in[z] and z not in DL_out[z]
        '''

    return