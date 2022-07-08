def union(r, p, u, v):
    link(p, r, find(p, u), find(p, v))


def link(p, r, u, v):
    if r[u] > r[v]:
        p[v] = u
    else:
        p[u] = v
        if r[u] == r[v]:
            r[v] += 1


def find(p, u):
    if u != p[u]:
        p[u] = find(p, p[u])
    return p[u]


def query(p, u, v):
    return find(p, u) == find(p, v)


