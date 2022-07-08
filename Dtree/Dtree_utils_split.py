# this file modifies delete_te and delete_te_simple functions in Dtree_utils.py
#  to keep track of merge of two components and splits of one component.

from Dtree.DTNode import DTNode
from queue import Queue
import sys

from Dtree.opt_utils import increment_size


def construct_BFS_tree(spanningtree, n, nte):
    root = None
    id2node = dict()
    visited = [False] * (n + 1)

    for u in spanningtree.keys():
        if visited[u]:
            continue
        visited[u] = True
        node = DTNode(u)
        id2node[u] = node
        if root == None:
            root = node
        q = Queue()
        q.put(u)
        while not q.empty():
            current_vertex = q.get()
            adj_vertices = spanningtree[current_vertex]
            current_node = id2node[current_vertex]
            for v in adj_vertices:
                if visited[v]:
                    continue
                visited[v] = True
                q.put(v)
                node_v = DTNode(v)
                id2node[v] = node_v
                current_node.children.add(node_v)
                node_v.parent = current_node

    for (a, b) in nte:
        id2node[a].nte.add(id2node[b])
        id2node[b].nte.add(id2node[a])

    return root, id2node


def reroot(n_w):

    if n_w.parent is None:
        return n_w

    c = n_w
    p = []  # keeps nodes in the path between the node and the root.
    while c is not None:
        p.append(c)  # p = p + c
        c = c.parent

    # swaps the parent/child relationship, and updates the size-attributes
    # p[i] and p[i - 1] is u_i and u_{i - 1}, respectively.
    for i in range(len(p) - 1, 0, -1):
        p[i].size -= p[i - 1].size
        p[i - 1].size += p[i].size

        p[i].parent = p[i - 1]
        p[i].children.remove(p[i - 1])
        p[i - 1].children.add(p[i])

    n_w.parent = None

    return n_w


def link(n_u, r_u, n_v):
    n_v.parent = n_u
    n_u.children.add(n_v)

    c = n_u
    new_root = None
    while c is not None:
        c.size += n_v.size

        if c.size > (r_u.size + n_v.size) // 2 and new_root is None and c.parent is not None:
            new_root = c

        c = c.parent
    if new_root is not None:
        r_u = reroot(new_root)
    return r_u


def insert_nte_simple(n_u, n_v):

    n_u.nte.add(n_v)
    n_v.nte.add(n_u)


def insert_nte(r, n_u, dist_u, n_v, dist_v):  # inserting a non tree edge
    # lvl(n_u) = dist_u, lvl(n_v) = dist_v
    #if (n_u.parent == n_v or n_v.parent == n_u) or not (n_u in n_v.nte and n_v in n_u.nte):
    #    return r
    if n_v in n_u.nte and n_u in n_v.nte:
        return

    if abs(dist_u - dist_v) < 2:  # no changes to BFS spanning tree
        n_u.nte.add(n_v)
        n_v.nte.add(n_u)
        return r
    else:
        if dist_u < dist_v:
            h = n_v
            l = n_u
        else:
            h = n_u
            l = n_v
        delta = abs(dist_u - dist_v) - 2
        c = h
        for i in range(1, delta):
            c = c.parent

        c.parent.nte.add(c)
        c.nte.add(c.parent)
        unlink(c)

        return link(l, r, reroot(h))


def insert_nontree_edge_BFS(u, steps_u, v, steps_v, root, id2node): #inserting a non tree edge
    node_u = id2node[u]
    node_v = id2node[v]

    node_u.nte.add(node_v)
    node_v.nte.add(node_u)
    if abs(steps_u - steps_v) <= 1:  # no changes to BFS spanning tree
        return 0
    else:
        if steps_u < steps_v:
            node = node_u
        else:
            node = node_v
        reconstruct_BFS_tree(node, id2node, set())
    return 0


def insert_te(n_u, n_v, r_u, r_v):

    # T1 includes v, T2 includes u
    if r_v.size < r_u.size:
        return link(n_u, r_u, reroot(n_v))
    else:
        return link(n_v, r_v, reroot(n_u))


def insert_te_simple(n_u, n_v, r_u, r_v):

    # T1 includes v, T2 includes u
    if r_v.size < r_u.size:
        r_v = reroot(n_v)

        n_u.children.add(r_v)
        r_v.parent = n_u
        c = n_u
        while c is not None:
            c.size += r_v.size
            c = c.parent
        return r_u
    else:
        r_u = reroot(n_u)

        n_v.children.add(r_u)
        r_u.parent = n_v
        c = n_v
        while c is not None:
            c.size += r_u.size
            c = c.parent
        return r_v


def insert_tree_edge_BFS(child, p, id2node):
    substree = reconstruct_BFS_tree(child, id2node, set())
    substree.parent = p
    p.children.add(substree)
    current = p

    while current is not None:
        current.size += substree.size
        current = current.parent
    return


def delete_nte(node_u, node_v):
    node_u.nte.remove(node_v)
    node_v.nte.remove(node_u)


def unlink(n_v):
    # n_v is a non-root node
    c = n_v
    while c.parent is not None:
        c = c.parent
        c.size -= n_v.size
    n_v.parent.children.remove(n_v)
    n_v.parent = None

    return n_v, c  # return n_v and the root


def delete_te_simple(n_u, n_v):
    # determine parent and child
    if n_u.parent == n_v:
        ch = n_u
    else:
        ch = n_v

    ch, root = unlink(ch)

    if ch.size < root.size:  # BFS is conducted on the smaller tree to find replacement edge.
        r_s = ch
        r_l = root
    else:
        r_s = root
        r_l = ch
    small_size = r_s.size
    n_rs, n_rl, beta = BFS_select_simple(r_s)

    if n_rs is None and n_rl is None:
        return r_s, r_l, 1
    else:
        n_rs.nte.remove(n_rl)
        n_rl.nte.remove(n_rs)

        return insert_te_simple(n_rs, n_rl, r_s, r_l), None, 0


def BFS_select_simple(r):
    # traverse the smaller tree to find all neighbors
    q = Queue()
    q.put(r)
    beta = 0
    while not q.empty(): # BFS
        node = q.get()
        if len(node.nte) > 0:
            for nte in node.nte:
                rt, _ = find_root(nte)
                beta += 1
                if rt.val == r.val:  # this non tree edge is included in the smaller tree.
                    continue
                return nte, node, beta
        for c_node in node.children:
            q.put(c_node)

    return None, None, beta


def delete_te(n_u, n_v):
    # determine parent and child
    if n_u.parent == n_v:
        ch = n_u
    else:
        ch = n_v

    ch, root = unlink(ch)

    if ch.size < root.size:  # BFS is conducted on the smaller tree to find replacement edge.
        r_s = ch
        r_l = root
    else:
        r_s = root
        r_l = ch

    small_size = r_s.size
    n_rs, n_rl, new_r, beta = BFS_select(r_s)

    if n_rs is None and n_rl is None:
        if new_r is not None:  # in smaller tree, new_r is the new root, reroot it.
            r_s = reroot(new_r)
        return r_s, r_l, 1
    else:
        n_rs.nte.remove(n_rl)
        n_rl.nte.remove(n_rs)

        return insert_te(n_rs, n_rl, r_s, r_l), None, 0


def BFS_select(r):
    # traverse the smaller tree to find all neighbors
    q = Queue()
    q.put(r)
    new_root = None  # new root for smaller tree if new_r is not None
    S = r.size  # size of smaller tree
    minimum_dist = sys.maxsize
    n_rs = None
    n_rl = None
    beta = 0
    while not q.empty():
        new_q = Queue()
        while not q.empty():
            node = q.get()
            if S > node.size > S // 2 and new_root is None:  # new root
                new_root = node
            if len(node.nte) > 0:
                for nte in node.nte:
                    rt, dist = find_root(nte)
                    beta += 1
                    if rt.val == r.val:  # this non tree edge is included in the smaller tree.
                        continue

                    # assert rt.val == R.val, "%d - %d errors in Deleting tree edges." %(rt.val, R.val)
                    if dist < minimum_dist:
                        minimum_dist = dist
                        n_rl = nte  # in larger tree
                        n_rs = node  # in smaller tree

            for c_node in node.children:
                q.put(c_node)
        q = new_q

    return n_rs, n_rl, new_root, beta


def query(n_u, n_v):

    d_u = None
    while n_u.parent is not None:
        d_u = n_u
        n_u = n_u.parent

    if d_u is not None and d_u.size > n_u.size // 2:
        n_u = reroot(d_u)

    d_v = None
    while n_v.parent is not None:
        d_v = n_v
        n_v = n_v.parent

    if d_v is not None and d_v.size > n_v.size // 2:
        n_v = reroot(d_v)

    return n_u.val == n_v.val


def query_simple(n_u, n_v):

    while n_u.parent is not None:
        n_u = n_u.parent

    while n_v.parent is not None:
        n_v = n_v.parent
    return n_u.val == n_v.val


def find_root(node):
    dist = 0
    while node.parent is not None:
        node = node.parent
        dist += 1
    return node, dist


def toRoot(node):
    dist = 0
    while node.parent is not None:
        node = node.parent
        dist += 1
    return dist


def reconstruct_BFS_tree(node, id2node, nodes_in_ST):

    q = Queue()
    S = []
    new_root = node

    q.put(node)
    visited = set()
    visited.add(node)
    old_parents_dict = dict()
    old_parents_dict[node] = node.parent  # save old parent pointer
    new_root.parent = None

    while not q.empty():
        current_node = q.get()
        current_node.size = 1
        S.append(current_node)
        for c_node in current_node.children.copy(): # children go first, because the children fields will be updated.
            old_parents_dict[c_node] = current_node
            if c_node in visited: # a tree edge becomes to a non tree edge
                current_node.children.remove(c_node)
                current_node.nte.add(c_node)
                c_node.nte.add(current_node)
            else:
                visited.add(c_node)
                q.put(c_node)

        if old_parents_dict[current_node] is not None:
            p = old_parents_dict[current_node]
            if p in visited:
                # p.children.remove(current_node.val)
                if not (current_node.parent == p or p.parent == current_node):  # becomes to a non tree edge
                    current_node.nte.add(p)
                    p.nte.add(current_node)
            else:   # remain a tree edge
                old_parents_dict[p] = p.parent  # save old parent pointer
                q.put(p)
                visited.add(p)
                # exchange parent and children relationship
                p.parent = current_node
                p.children.remove(current_node)
                current_node.children.add(p)

        for t_node in current_node.nte.copy():
            if t_node in nodes_in_ST or t_node in visited:
                continue
            old_parents_dict[t_node] = t_node.parent    # save old parent pointer
            t_node.parent = current_node
            current_node.children.add(t_node)

            q.put(t_node)
            visited.add(t_node)

            current_node.nte.remove(t_node)
            t_node.nte.remove(current_node)

    while len(S)> 0:
        cur = S.pop()
        if cur.parent is not None:
            cur.parent.size += cur.size

    return new_root


def reconstruct_BFS_tree1(node, id2node, nodes_in_ST):

    q = Queue()
    new_root = node

    q.put(node)
    visited = set()
    visited.add(node)
    old_parents_dict = dict()
    old_parents_dict[node] = node.parent  # save old parent pointer
    new_root.parent = None

    while not q.empty():
        new_q = Queue()
        while not q.empty():
            current_node = q.get()
            for c_node in current_node.children.copy(): # children go first, because the children fields will be updated.
                old_parents_dict[c_node] = current_node
                if c_node in visited: # a tree edge becomes to a non tree edge
                    current_node.children.remove(c_node)
                    current_node.nte.add(c_node)
                    c_node.nte.add(current_node)
                else:
                    visited.add(c_node)
                    new_q.put(c_node)

            if old_parents_dict[current_node] is not None:
                p = old_parents_dict[current_node]
                if p in visited:
                    # p.children.remove(current_node.val)
                    if not (current_node.parent == p or p.parent == current_node):    # becomes to a non tree edge
                        current_node.nte.add(p)
                        p.nte.add(current_node)
                else: # remain a tree edge
                    old_parents_dict[p] = p.parent  # save old parent pointer
                    new_q.put(p)
                    visited.add(p)
                    # exchange parent and children relationship
                    p.parent = current_node
                    p.children.remove(current_node)
                    current_node.children.add(p)

            for t_node in current_node.nte.copy():
                if t_node not in nodes_in_ST or t_node in visited:
                    continue
                old_parents_dict[t_node] = t_node.parent # save old parent pointer
                t_node.parent = current_node
                current_node.children.add(t_node)

                new_q.put(t_node)
                visited.add(t_node)

                current_node.nte.remove(t_node)
                t_node.nte.remove(current_node)

            current_node.size = 0
            increment_size(current_node)

        q = new_q

    return new_root


def delete_tree_edge_BFS(u, v, id2node):
    node_u = id2node[u]
    node_v = id2node[v]

    #(u, v) is a tree edge
    if node_u.parent == node_v:
        node_u.parent = None
        node_v.children.remove(node_u)

        # update size
        current = node_v
        while current is not None:
            current.size -= node_u.size
            current = current.parent

        r1, _ = find_root(v, id2node)
        r2 = node_u
    else: #node_v.parent == node_u
        node_v.parent = None
        node_u.children.remove(node_v)

        # update size
        current = node_u
        while current is not None:
            current.size -= node_v.size
            current = current.parent
        r1, _ = find_root(u, id2node)
        r2 = node_v

    if r1.size < r2.size: # r is the root of smaller tree
        r = r1
    else:
        r = r2

    # traverse the smaller tree to find all neighbors
    q = Queue()
    candidates = set()
    q.put(r)
    nodes_in_ST = set()
    neighbors = set()
    neighbors_dict = dict()
    q.put(r)
    while not q.empty():
        node = q.get()
        nodes_in_ST.add(node)
        if len(node.nte) > 0:
            neighbors.update(node.nte)
            for t_node in node.nte:
                neighbors_dict[t_node] = node
        for c_node in node.children:
            q.put(c_node)

    replacements = neighbors - (nodes_in_ST & neighbors) # neighbors that are replacements
    if len(replacements) == 0:
        return
    else:
        # attach subtree rooted at a to node_b
        b = None

        min_dist = sys.maxsize
        for t_node in replacements:
            _, dist = find_root(t_node.val, id2node)

            if dist < min_dist:
                min_dist = dist
                b = t_node

        node_a = neighbors_dict[b]

        if node_a != r:
            node_a = reconstruct_BFS_tree(node_a, id2node, nodes_in_ST)
        node_b = id2node[b]

        node_a.nte.remove(node_b)
        node_b.nte.remove(node_a)

        node_b.children.add(node_a)
        node_a.parent = node_b
        # update size
        current = node_b
        while current is not None:
            current.size += node_a.size
            current = current.parent

        return


def validBFStree(root, id2node):
    q = Queue()
    q.put(root)
    count = 0
    while not q.empty():
        node = q.get()
        count += 1
        for c in node.children:
            q.put(id2node[c])

    if count != root.size:
        return False

    for c in root.children:
        if not validBFStree(id2node[c], id2node):
            return False

    return True


def printBFStree(root):
    q = Queue()
    q.put(root)
    idx = 0
    print("print tree by level.")
    while not q.empty():
        new_q = Queue()
        str = []
        while not q.empty():
            node = q.get()
            tmp = []
            for inc_nte in node.nte:
                tmp.append(inc_nte.val)
            str.append((node.val, tmp, node.size))
            for adj_node in node.children:
                new_q.put(adj_node)
        print("%d level" %idx, str)
        idx += 1
        q = new_q
