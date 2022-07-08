from _collections import defaultdict
from HK.HKNode import HKNode
from ET.ET_utils import obtainETRs, constructST_adjacency_list
import random


def order(a, b):
    if a < b:
        return a, b
    else:
        return b, a


def HK_constructSF(graph, n, max_priority):
    forest = set()
    st, tree_edges, non_tree_edges = constructST_adjacency_list(graph, n)
    etrs = obtainETRs(st, n)
    active_occurrence_dict, tree_edges_pointers = ET_treeHK(etrs, non_tree_edges, forest, max_priority)
    return forest, tree_edges, non_tree_edges, active_occurrence_dict, tree_edges_pointers


def ET_treeHK(etrs, non_tree_edges, forest, max_priority):
    active_occurrence_dict = defaultdict()
    tree_edges_pointers = defaultdict(list)

    nodes_list = []
    # construct ETR-node
    for etr in etrs:
        nodes = generate_NodeHK(etr, max_priority, active_occurrence_dict, tree_edges_pointers)
        nodes_list.append(nodes)

    # update non-tree-edges information. One condition: all active occurrences are selected
    for (a, b) in non_tree_edges:
        active_occurrence_dict[a].incident_non_tree_edge.add(b)
        active_occurrence_dict[b].incident_non_tree_edge.add(a)

    #construct ET-trees
    for nodes in nodes_list:
        root = construct_ET_treeHK(nodes, 0, len(nodes) - 1)
        forest.add(root)

    return active_occurrence_dict, tree_edges_pointers


def construct_ET_treeHK(nodes, low, high):
    if low > high:
        return None
    elif low == high:
        current_node = nodes[low]
        current_node.weight = len(current_node.incident_non_tree_edge)
        return current_node
    else:
        idx = low
        for i in range(low, high + 1):
            if nodes[i].priority > nodes[idx].priority:
                idx = i
        current_node = nodes[idx]
        l_child = construct_ET_treeHK(nodes, low, idx - 1)
        l_child_size = 0
        l_child_weight = 0
        if l_child is not None:
            l_child.parent = current_node
            current_node.left = l_child
            l_child_size = l_child.size
            l_child_weight = l_child.weight
        r_child = construct_ET_treeHK(nodes, idx + 1, high)
        r_child_size = 0
        r_child_weight = 0
        if r_child is not None:
            r_child.parent = current_node
            current_node.right = r_child
            r_child_size = r_child.size
            r_child_weight = r_child.weight
        if current_node.active:
            current_node.size = 1 + l_child_size + r_child_size
        else:
            current_node.size = l_child_size + r_child_size
        current_node.weight = l_child_weight + r_child_weight + len(current_node.incident_non_tree_edge)
        return current_node


def generate_NodeHK(etr, max_priority, active_occurrence_dict, tree_edges_pointers):
    nodes_list = list()

    for i in range(len(etr)):
        occurrence = etr[i]
        node = HKNode(occurrence, random.randint(1, max_priority))
        node.val = occurrence
        if occurrence not in active_occurrence_dict:
            node.active = True
            active_occurrence_dict[occurrence] = node
            node.size = 1

        # construct tree_edge_pointer
        nodes_list.append(node)
        if i > 0:
            (u, v) = order(nodes_list[i - 1].val, occurrence)  # (u, v) and (v, u) are the same edge
            if (u, v) in tree_edges_pointers:
                if tree_edges_pointers[(u, v)][-1] != nodes_list[i - 1]:
                    tree_edges_pointers[(u, v)].append(nodes_list[i - 1])
                tree_edges_pointers[(u, v)].append(node)
            else:
                tree_edges_pointers[(u, v)].append(nodes_list[i - 1])
                tree_edges_pointers[(u, v)].append(node)

    return nodes_list


def valid_randomized_BST(root):
    if root is None:
        return True

    if root.left is not None and root.priority < root.left.priority:
        return False

    if root.right is not None and root.priority < root.right.priority:
        return False

    return valid_randomized_BST(root.left) & valid_randomized_BST(root.right)
