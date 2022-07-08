class UFNode:

    def __init__(self, v):
        self.key = v
        self.rank = 0
        self.parent = None


def find_set(x):
    if x.parent is None:
        return x

    if x != x.parent:
        x.parent = find_set(x.parent)
    return x.parent


def link_node(x, y):
    if x.rank > y.rank:
        y.parent = x
    else:
        x.parent = y
        if x.rank == y.rank:
            y.rank += 1


def union_node(x, y):
    link_node(find_set(x), find_set(y))
