"""
This file is a python implementation of Henzinger-King's algorithm
Monika Rauch Henzinger and Valerie King. 1999. Randomized Fully Dynamic Graph
Algorithms with Polylogarithmic Time per Operation
"""

import math
from timeit import default_timer as timer
from HK.HKNode import HKNode
from utils.tree_utils import coding, smaller, sort
from utils.graph_utils import order
import sys, random, queue


def sort1(tree_edge_pointer):
    maximum = 0
    minimum = 0
    codes = []
    for pointer in tree_edge_pointer:
        codes.append(coding(pointer))
    for i in range(1, len(tree_edge_pointer)):
        if smaller(codes[maximum], codes[i]):
            maximum = i
        if smaller(codes[i], codes[minimum]):
            minimum = i

    items = []
    for i in range(0, len(tree_edge_pointer)):
        if i == maximum or i == minimum:
            continue
        items.append(i)
    if len(items) == 1:
        return tree_edge_pointer[minimum], tree_edge_pointer[items[0]], tree_edge_pointer[maximum]
    elif smaller(codes[items[0]], codes[items[-1]]):
        return tree_edge_pointer[minimum], tree_edge_pointer[items[-1]], tree_edge_pointer[maximum]
    else:
        return tree_edge_pointer[minimum], tree_edge_pointer[items[0], tree_edge_pointer[maximum]]


def rotateRight(x, root):
    p = x.parent
    g = None
    if p.parent is not None:
        g = p.parent
        if g.left == p:
            g.left = x
        else:
            g.right = x
        x.parent = g
    else:
        x.parent = None

    p.weight = p.weight - x.weight
    p.size = p.size - x.size

    # cut right branch of x
    x_right = x.right
    x_right_weight = 0
    x_right_size = 0
    if x_right is not None:
        x_right_weight = x_right.weight
        x_right_size = x_right.size
    x.weight -= x_right_weight
    x.size -= x_right_size

    # attach right branch of x to p
    if x_right is not None:
        x_right.parent = p

    p.left = x_right
    p.size += x_right_size
    p.weight += x_right_weight

    # attach p as the right branch of x
    x.right = p
    p.parent = x
    x.size += p.size
    x.weight += p.weight

    if g is not None:
        return root
    else:
        return x


def rotateLeft(x, root):
    p = x.parent
    g = None
    if p.parent is not None:
        g = p.parent
        if g.left == p:
            g.left = x
        else:
            g.right = x
        x.parent = g
    else:
        x.parent = None

    p.weight = p.weight - x.weight
    p.size = p.size - x.size

    # cut left branch of x
    x_left = x.left
    x_left_weight = 0
    x_left_size = 0
    if x_left is not None:
        x_left_weight = x_left.weight
        x_left_size = x_left.size

    x.weight -= x_left_weight
    x.size -= x_left_size

    # attach left branch of x to p
    if x_left is not None:
        x_left.parent = p

    p.right = x_left
    p.size += x_left_size
    p.weight += x_left_weight

    # attach p as the left branch of x
    x.left = p
    p.parent = x
    x.size += p.size
    x.weight += p.weight

    if g is not None:
        return root
    else:
        return x


def rotate_to_root(x, root):
    c = 0
    while x != root:
        p = x.parent
        if x == p.left:
            root = rotateRight(x, root)
        else:
            root = rotateLeft(x, root)
        c += 1
    return x, c


def head_of_etr_tree(root):
    pointer = root
    while pointer.left is not None:
        pointer = pointer.left
    return pointer


def tail_of_etr_tree(root):
    pointer = root
    while pointer.right is not None:
        pointer = pointer.right
    return pointer


def split_before(root, current_node):
    node = HKNode(-1, sys.maxsize)
    if current_node.left is None:
        current_node.left = node
        node.parent = current_node
    else:
        pointer = current_node.left
        while pointer.right is not None:
            pointer = pointer.right
        pointer.right = node
        node.parent = pointer

    root, c = rotate_to_root(node, root)
    left_branch = root.left
    left_branch.parent = None

    right_branch = root.right
    right_branch.parent = None

    return left_branch, right_branch


def split_after(root, current_node):
    node = HKNode(-1, sys.maxsize)
    if current_node.right is None:
        current_node.right = node
        node.parent = current_node
    else:
        pointer = current_node.right
        while pointer.left is not None:
            pointer = pointer.left
        pointer.left = node
        node.parent = pointer

    root, c = rotate_to_root(node, root)

    left_branch = root.left
    left_branch.parent = None

    right_branch = root.right
    right_branch.parent = None

    return left_branch, right_branch


def predecessor(current_node):
    if current_node.left is not None:
        pred = current_node.left
        while pred.right is not None:
            pred = pred.right
        return pred
    else:
        if current_node.parent is None:
            return None
        else:
            parent_pointer = current_node.parent
            current_pointer = current_node
            while parent_pointer is not None:
                if current_pointer == parent_pointer.right:
                    return parent_pointer
                current_pointer = parent_pointer
                parent_pointer = parent_pointer.parent
            return None


def successor(current_node):
    if current_node.right is not None:
        succ = current_node.right
        while succ.left is not None:
            succ = succ.left
        return succ
    else:
        if current_node.parent is None:
            return None
        else:
            parent_pointer = current_node.parent
            current_pointer = current_node
            while parent_pointer is not None:
                if current_pointer == parent_pointer.left:
                    return parent_pointer
                current_pointer = parent_pointer
                parent_pointer = parent_pointer.parent
        return None


def rotate_to_leaf(current_node, root):
    while current_node.left is not None or current_node.right is not None:
        if current_node.left is not None and current_node.right is not None:
            if current_node.left.priority > current_node.right.priority:
                root = rotateRight(current_node.left, root)
            else:
                root = rotateLeft(current_node.right, root)
        elif current_node.left is not None:
            root = rotateRight(current_node.left, root)
        else:
            root = rotateLeft(current_node.right, root)

    return current_node, root


def merge(r1, r2):
    root = HKNode(-1, sys.maxsize)
    root.size = r1.size + r2.size
    root.weight = r1.weight + r2.weight
    root.left = r1
    root.right = r2
    r1.parent = root
    r2.parent = root

    current_node = root

    # rotate root to leaf
    current_node, root = rotate_to_leaf(current_node, root)

    p = current_node.parent
    if p.left == current_node:
        p.left = None
    else:
        p.right = None

    return root


def merge_update_pointer(r1, rightmost_r1, r2, leftmost_r2, tree_edges_pointer):
    if rightmost_r1 is None:
        rightmost_r1 = r1
        while rightmost_r1.right is not None:
            rightmost_r1 = rightmost_r1.right

    if leftmost_r2 is None:
        leftmost_r2 = r2
        while leftmost_r2.left is not None:
            leftmost_r2 = leftmost_r2.left

    if rightmost_r1.active:
        succ_leftmost_r2 = successor(leftmost_r2)
        if succ_leftmost_r2 is None:
            del r2
            return r1
        (u, v) = order(succ_leftmost_r2.val, leftmost_r2.val)
        tree_edges_pointer[(u, v)].remove(leftmost_r2)
        leftmost_r2, r2 = rotate_to_leaf(leftmost_r2, r2)
        p = leftmost_r2.parent
        if leftmost_r2 == p.left:
            p.left = None
        else:
            p.right = None
        del leftmost_r2
        if rightmost_r1 not in tree_edges_pointer[(u, v)]:
            tree_edges_pointer[(u, v)].append(rightmost_r1)
    else:
        pred_rightmost_r1 = predecessor(rightmost_r1)
        if pred_rightmost_r1 is None:
            del r1
            return r2

        (u, v) = order(pred_rightmost_r1.val, rightmost_r1.val)

        tree_edges_pointer[(u, v)].remove(rightmost_r1)
        rightmost_r1, r1 = rotate_to_leaf(rightmost_r1, r1)
        p = rightmost_r1.parent
        if rightmost_r1 == p.left:
            p.left = None
        else:
            p.right = None
        del rightmost_r1
        if leftmost_r2 not in tree_edges_pointer[(u, v)]:
            tree_edges_pointer[(u, v)].append(leftmost_r2)

    root = merge(r1, r2)
    return root


def reroot(root, u, active_occurrence_dict, tree_edges_pointers, max_priority):
    head = head_of_etr_tree(root)
    if head.val == u:
        return root

    pred_u = predecessor(active_occurrence_dict[u])
    succ_u = successor(active_occurrence_dict[u])

    root_left_branch, root_right_branch = split_before(root, active_occurrence_dict[u])

    node = HKNode(u, random.randint(1, max_priority))

    # attach node in the end of ETR-tree
    tail_of_left_branch = tail_of_etr_tree(root_left_branch)
    tail_of_left_branch.right = node
    node.parent = tail_of_left_branch

    # rotate node to the place,which does not violate the priority value
    p = tail_of_left_branch
    while p is not None and node.priority > p.priority:
        if node == p.right:
            root_left_branch = rotateLeft(node, root_left_branch)
        else:
            root_left_branch = rotateRight(node, root_left_branch)
        p = node.parent

    # update tree-edge pointers
    (a, b) = order(pred_u.val, u)
    if pred_u.val != succ_u.val:
        tree_edges_pointers[(a, b)].remove(active_occurrence_dict[u])
    tree_edges_pointers[(a, b)].append(node)

    root = merge_update_pointer(root_right_branch, None, root_left_branch, None, tree_edges_pointers)

    return root


def insert_tree_edge(a, root_a, b, root_b, tree_edges, active_occurrence_dict, tree_edges_pointers, max_priority):
    # for update tree_edges and non_tree_edges, rename (a, b) to (x, y) for one-time use
    (x, y) = order(a, b)

    tree_edges.add((x, y))
    if root_a is None:
        root_a = find_root(active_occurrence_dict[a])
    if root_b is None:
        root_b = find_root(active_occurrence_dict[b])

    root_a = reroot(root_a, a, active_occurrence_dict, tree_edges_pointers, max_priority)
    root_b = reroot(root_b, b, active_occurrence_dict, tree_edges_pointers, max_priority)

    tail_of_root_a = tail_of_etr_tree(root_a)
    head_of_root_b = head_of_etr_tree(root_b)

    # add a new occurrence of root_a to the end new ETR
    node = HKNode(a, random.randint(1, max_priority))

    # update tree-edge-pointers
    tree_edges_pointers[(x, y)].append(tail_of_root_a)
    tree_edges_pointers[(x, y)].append(head_of_root_b)
    if root_b.left is not None or root_b.right is not None:
        tail_of_root_b = tail_of_etr_tree(root_b)
        tree_edges_pointers[(x, y)].append(tail_of_root_b)

    tree_edges_pointers[(x, y)].append(node)
    #print("appending new node takes %f" % (time.clock() - t))

    #t = time.clock()
    # attach node in the end of ETR-tree
    tail_of_root_b = tail_of_etr_tree(root_b)
    tail_of_root_b.right = node
    node.parent = tail_of_root_b
    ##
    # rotate node to the place,which does not violate the priority value
    p = tail_of_root_b
    while p is not None and node.priority > p.priority:
        if node == p.right:
            root_b = rotateLeft(node, root_b)
        else:
            root_b = rotateRight(node, root_b)
        p = node.parent

    root = merge(root_a, root_b)

    return root


def insert_nontree_edge(u, v, active_occurrence_dict, non_tree_edges):

    #if v in u_representive.nte != u in v_representive.nte:
    #   raise ValueError("Errors in inserting nontree edges")

    u_representive = active_occurrence_dict[u]
    v_representive = active_occurrence_dict[v]

    # exclude mutil-edges of two vertices
    if v in u_representive.nte and u in v_representive.nte:
        return

    u_representive.nte.add(v)
    pointer = u_representive
    while pointer is not None:
        pointer.weight += 1
        pointer = pointer.parent

    v_representive.nte.add(u)
    pointer = v_representive
    while pointer is not None:
        pointer.weight += 1
        pointer = pointer.parent

    non_tree_edges.add((u, v))

    return


def delete_nontree_edge(u, v, active_occurrence_dict, non_tree_edges):

    active_occurrence_dict[u].nte.remove(v)
    # update weight
    pointer = active_occurrence_dict[u]
    while pointer is not None:
        pointer.weight -= 1
        pointer = pointer.parent

    active_occurrence_dict[v].nte.remove(u)
    # update weight
    pointer = active_occurrence_dict[v]
    while pointer is not None:
        pointer.weight -= 1
        pointer = pointer.parent

    non_tree_edges.remove((u, v))


def delete_tree_edge(u, v, tree_edges, non_tree_edges, active_occurrence_dict, tree_edges_pointers, max_priority):
    root_u = find_root(active_occurrence_dict[u])
    root = root_u
    edge = order(u, v)
    first_pointer, last_pointer = sort(tree_edges_pointers[edge])
    s1, right_branch = split_after(root, first_pointer)
    s2, s3 = split_before(right_branch, last_pointer)
    r2 = s2
    r1 = merge_update_pointer(s1, first_pointer, s3, last_pointer, tree_edges_pointers)

    # clean up tree_edges_pointers
    del tree_edges_pointers[edge]

    tree_edges.remove((u, v))

    # find the replacement edge
    #start = timer()
    a, root_of_a, b, root_of_b, small_size, beta = find_replacement(r1, r2, active_occurrence_dict)
    #t = timer() - start

    # no replacement edges are found.
    if a is None and root_of_a is None and b is None and root_of_b is None:
        return small_size, beta

    # delete non-tree edge (a, b)
    t_a, t_b = order(a, b)
    delete_nontree_edge(t_a, t_b, active_occurrence_dict, non_tree_edges)

    # insert replacement edge
    insert_tree_edge(a, root_of_a, b, root_of_b, tree_edges, active_occurrence_dict, tree_edges_pointers, max_priority)

    return small_size, beta


def find_replacement(r1, r2, active_occurrence_dict):

    if r1.weight < r2.weight:
        r = r1
    else:
        r = r2

    w_r = r.weight
    n = r.size

    small_size = r.size
    # find all candidates
    candidates = nontree_edges(r)

    c = 16  # predefined
    log_n_square = int(math.pow(math.log(n, 2), 2))
    sample_max = c * int(math.log(n, 2))

    beta = 0
    if len(candidates) == 0:
        return None, None, None, None, small_size, beta

    # sampling optimization
    if w_r > log_n_square:
        for _ in range(sample_max):
            sample_res = sample_test(candidates.copy(), active_occurrence_dict)
            beta += 2
            if sample_res is not None:
                (a, root_of_a, b, root_of_b) = sample_res
                return a, root_of_a, b, root_of_b, small_size, beta

    for (a, b) in candidates:
        root_of_a = find_root(active_occurrence_dict[a])
        root_of_b = find_root(active_occurrence_dict[b])
        beta += 2
        if root_of_a != root_of_b:
            return a, root_of_a, b, root_of_b, small_size, beta

    return None, None, None, None, small_size, beta


def nontree_edges(root):
    # root of an ETR-tree
    if root.size == 0:
        return []
    ntes = []
    q = queue.Queue()
    q.put(root)
    while q.qsize() > 0:
        node = q.get()
        if len(node.nte) > 0:
            for endpoint in node.nte:
                ntes.append([node.val, endpoint])
        if node.left is not None and node.left.weight > 0:
            q.put(node.left)
        if node.right is not None and node.right.weight > 0:
            q.put(node.right)

    return ntes


def sample_test(candidates, active_occurrence_dict):
    # root of an ETR-tree
    (a, b) = random.choice(candidates)
    root_of_a = find_root(active_occurrence_dict[a])
    root_of_b = find_root(active_occurrence_dict[b])

    if root_of_a != root_of_b:
        return a, root_of_a, b, root_of_b
    else:
        return None


def find_root(node):
    p = node

    while p.parent is not None:
        p = p.parent
    return p
